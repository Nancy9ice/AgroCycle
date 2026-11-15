"use client";

import "maplibre-gl/dist/maplibre-gl.css";
import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { ringFromCorners } from "./boundary-draft";
import { emptyCollection, ringBounds, ringsToPolygons, type Bounds } from "./map-data";
import type { County, LonLat } from "./types";

/** Copied from node_modules by scripts/copy-maplibre-worker.mjs. */
const WORKER_URL = "/vendor/maplibre/maplibre-gl-worker.mjs";
const IMAGERY_TILES =
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
const IMAGERY_ATTRIBUTION =
  "Imagery © Esri, Maxar, Earthstar Geographics, and the GIS User Community";

export interface DrawMapApi {
  /** The point under the crosshair. */
  getCentre: () => LonLat;
}

export interface MapFocus {
  position: LonLat;
  zoom: number;
  /** Changes on every request, so asking for the same place twice still moves the map. */
  nonce: number;
}

interface DrawMapProps {
  counties: readonly County[];
  corners: readonly LonLat[];
  /** The farmer's own position, shown as a dot. Never sent anywhere. */
  here: LonLat | null;
  focus: MapFocus | null;
  /** When false the map still pans and zooms, but taps no longer add corners. */
  drawing: boolean;
  onAddCorner: (corner: LonLat) => void;
  onReady: (api: DrawMapApi) => void;
  className?: string;
}

const prefersReducedMotion = () =>
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const tokenColour = (name: string, fallback: string) =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;

function draftData(corners: readonly LonLat[]) {
  const points: GeoJSON.FeatureCollection = {
    type: "FeatureCollection",
    features: corners.map((corner, index) => ({
      type: "Feature",
      properties: { n: index + 1 },
      geometry: { type: "Point", coordinates: [...corner] },
    })),
  };
  const path: GeoJSON.FeatureCollection = {
    type: "FeatureCollection",
    features:
      corners.length >= 2
        ? [
            {
              type: "Feature",
              properties: {},
              geometry: { type: "LineString", coordinates: corners.map((c) => [...c]) },
            },
          ]
        : [],
  };
  const ring = ringFromCorners(corners);
  const area: GeoJSON.FeatureCollection = {
    type: "FeatureCollection",
    features: ring.length
      ? [
          {
            type: "Feature",
            properties: {},
            geometry: { type: "Polygon", coordinates: [ring.map((c) => [...c])] },
          },
        ]
      : [],
  };
  return { points, path, area };
}

/**
 * Satellite map for drawing a field. One tap adds a corner. The crosshair in the middle lets someone
 * pan, then press a button to add a corner exactly there, which is steadier than tapping on a phone and
 * works from the keyboard. One finger scrolls the page (two move the map), so the page never gets stuck.
 */
export function DrawMap({
  counties,
  corners,
  here,
  focus,
  drawing,
  onAddCorner,
  onReady,
  className,
}: DrawMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [ready, setReady] = useState(false);
  const [imageryFailed, setImageryFailed] = useState(false);

  // Latest callbacks and state, without rebuilding the map.
  const onAddCornerRef = useRef(onAddCorner);
  const drawingRef = useRef(drawing);
  const onReadyRef = useRef(onReady);
  useEffect(() => {
    onAddCornerRef.current = onAddCorner;
    drawingRef.current = drawing;
    onReadyRef.current = onReady;
  }, [onAddCorner, drawing, onReady]);

  useEffect(() => {
    let cancelled = false;
    let map: MapLibreMap | undefined;

    async function init() {
      const maplibregl = await import("maplibre-gl");
      if (cancelled || !containerRef.current) return;
      maplibregl.setWorkerUrl(WORKER_URL);

      const bounds: Bounds = ringBounds(counties.map((county) => county.ring));
      const white = tokenColour("--color-surface", "#ffffff");
      const ink = tokenColour("--color-forest-950", "#0e2616");
      const accent = tokenColour("--color-harvest-500", "#d9a02f");

      const instance = new maplibregl.Map({
        container: containerRef.current,
        bounds: [
          [bounds[0], bounds[1]],
          [bounds[2], bounds[3]],
        ],
        fitBoundsOptions: { padding: 24 },
        attributionControl: { compact: true },
        cooperativeGestures: true,
        style: {
          version: 8,
          sources: {
            imagery: {
              type: "raster",
              tiles: [IMAGERY_TILES],
              tileSize: 256,
              maxzoom: 19,
              attribution: IMAGERY_ATTRIBUTION,
            },
            counties: {
              type: "geojson",
              data: ringsToPolygons(counties.map((c) => c.ring)),
            },
            "draft-area": { type: "geojson", data: emptyCollection },
            "draft-path": { type: "geojson", data: emptyCollection },
            "draft-points": { type: "geojson", data: emptyCollection },
            here: { type: "geojson", data: emptyCollection },
          },
          layers: [
            { id: "backdrop", type: "background", paint: { "background-color": ink } },
            { id: "imagery", type: "raster", source: "imagery" },
            {
              id: "counties-line",
              type: "line",
              source: "counties",
              paint: { "line-color": white, "line-width": 2, "line-opacity": 0.85 },
            },
            {
              id: "draft-fill",
              type: "fill",
              source: "draft-area",
              paint: { "fill-color": accent, "fill-opacity": 0.3 },
            },
            {
              id: "draft-casing",
              type: "line",
              source: "draft-path",
              paint: { "line-color": ink, "line-width": 6 },
            },
            {
              id: "draft-line",
              type: "line",
              source: "draft-path",
              paint: { "line-color": white, "line-width": 3 },
            },
            {
              id: "draft-corners",
              type: "circle",
              source: "draft-points",
              paint: {
                "circle-radius": 7,
                "circle-color": accent,
                "circle-stroke-width": 3,
                "circle-stroke-color": white,
              },
            },
            {
              id: "here-halo",
              type: "circle",
              source: "here",
              paint: {
                "circle-radius": 16,
                "circle-color": "rgba(255,255,255,0.25)",
                "circle-stroke-width": 2,
                "circle-stroke-color": white,
              },
            },
            {
              id: "here-dot",
              type: "circle",
              source: "here",
              paint: { "circle-radius": 6, "circle-color": ink },
            },
          ],
        },
      });

      map = instance;
      mapRef.current = instance;
      instance.addControl(
        new maplibregl.NavigationControl({ showCompass: false }),
        "top-right",
      );
      instance.on("click", (event) => {
        if (!drawingRef.current) return;
        onAddCornerRef.current([event.lngLat.lng, event.lngLat.lat]);
      });
      instance.on("error", (event) => {
        const status = (event.error as { status?: number } | undefined)?.status;
        if (status !== undefined) setImageryFailed(true);
      });
      // Ready as soon as the style is in, not when every satellite picture has arrived: on a slow
      // connection the pictures can take a long time, and drawing must not wait for them.
      let announced = false;
      const markReady = () => {
        if (cancelled || announced) return;
        announced = true;
        setReady(true);
        onReadyRef.current({
          getCentre: () => {
            const centre = instance.getCenter();
            return [centre.lng, centre.lat];
          },
        });
      };
      instance.on("style.load", markReady);
      instance.on("load", markReady);
      if (instance.isStyleLoaded()) markReady();
    }

    void init();
    return () => {
      cancelled = true;
      map?.remove();
      mapRef.current = null;
    };
  }, [counties]);

  // Corners drawn so far.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const data = draftData(corners);
    (map.getSource("draft-points") as GeoJSONSource).setData(data.points);
    (map.getSource("draft-path") as GeoJSONSource).setData(data.path);
    (map.getSource("draft-area") as GeoJSONSource).setData(data.area);
  }, [corners, ready]);

  // The farmer's own position.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    (map.getSource("here") as GeoJSONSource).setData(
      here
        ? {
            type: "FeatureCollection",
            features: [
              {
                type: "Feature",
                properties: {},
                geometry: { type: "Point", coordinates: [...here] },
              },
            ],
          }
        : emptyCollection,
    );
  }, [here, ready]);

  // Move the map when asked.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !focus) return;
    map.flyTo({
      center: [...focus.position],
      zoom: focus.zoom,
      duration: prefersReducedMotion() ? 0 : 900,
    });
  }, [focus, ready]);

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-[var(--radius-card)] border border-line bg-forest-950",
        className,
      )}
    >
      <div
        ref={containerRef}
        role="application"
        aria-label="Satellite map for drawing your field. Use the buttons under the map to add corners."
        // Inline, because MapLibre's own stylesheet sets `position: relative` on its container and would
        // beat a utility class, collapsing the map to its default 300 px strip.
        style={{ position: "absolute", inset: 0 }}
      />
      {ready ? (
        <svg
          aria-hidden
          viewBox="0 0 40 40"
          className="pointer-events-none absolute top-1/2 left-1/2 size-10 -translate-x-1/2 -translate-y-1/2"
        >
          <g stroke="#0e2616" strokeWidth="4.5" strokeLinecap="round">
            <path d="M20 4v10M20 26v10M4 20h10M26 20h10" />
          </g>
          <g stroke="#ffffff" strokeWidth="2" strokeLinecap="round">
            <path d="M20 4v10M20 26v10M4 20h10M26 20h10" />
          </g>
        </svg>
      ) : (
        <div
          aria-busy
          className="absolute inset-0 grid place-items-center text-sm text-white/80"
        >
          Loading the map…
        </div>
      )}
      {imageryFailed ? (
        <p
          role="status"
          className="absolute inset-x-3 bottom-8 rounded-xl bg-surface/95 px-3 py-2 text-sm text-ink shadow-card"
        >
          The satellite pictures did not load. You can still add corners, but the map is
          blank.
        </p>
      ) : null}
    </div>
  );
}
