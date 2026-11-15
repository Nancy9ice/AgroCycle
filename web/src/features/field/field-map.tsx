"use client";

import "maplibre-gl/dist/maplibre-gl.css";
import type {
  ExpressionSpecification,
  GeoJSONSource,
  Map as MapLibreMap,
} from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import { evidenceTypes, type EvidenceTypeId } from "@/domain/evidence";
import { cn } from "@/lib/cn";
import { PRIMARY_FIELD_ID } from "./data";
import { flightLabel, imageryImageUrl } from "./imagery";
import { useFieldImagery } from "./use-field-imagery";
import {
  emptyCollection,
  fieldPoints,
  fieldPolygons,
  ringBounds,
  ringsToPolygons,
  type Bounds,
  type MarkerKind,
} from "./map-data";
import type { County, CountyName, DemoField } from "./types";

/** Copied from node_modules by scripts/copy-maplibre-worker.mjs. */
const WORKER_URL = "/vendor/maplibre/maplibre-gl-worker.mjs";

const IMAGERY_TILES =
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
const IMAGERY_ATTRIBUTION =
  "Imagery © Esri, Maxar, Earthstar Geographics, and the GIS User Community";

/** Below this zoom fields are a few pixels wide, so they are drawn as markers instead. */
const OUTLINE_ZOOM = 12;

export type CountyFilter = "all" | CountyName;

interface FieldMapProps {
  fields: readonly DemoField[];
  counties: readonly County[];
  selectedId: string;
  countyFilter: CountyFilter;
  onSelect: (id: string) => void;
  className?: string;
}

/** Map colours come from the CSS design tokens, so the map and the UI never drift apart. */
function readTokens() {
  const style = getComputedStyle(document.documentElement);
  const token = (name: string, fallback: string) =>
    style.getPropertyValue(name).trim() || fallback;
  return {
    backdrop: token("--color-forest-950", "#0e2616"),
    ink: token("--color-forest-950", "#0e2616"),
    white: token("--color-surface", "#ffffff"),
    primary: token("--color-harvest-500", "#d9a02f"),
    rotation: token("--color-surface", "#ffffff"),
    rotationStroke: token("--color-forest-700", "#235032"),
    edge: token("--color-clay-100", "#f4e2d9"),
    edgeStroke: token("--color-clay-700", "#8f432a"),
  };
}

const prefersReducedMotion = () =>
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const kindMatch = (values: Record<MarkerKind, string>): ExpressionSpecification => [
  "match",
  ["get", "kind"],
  "primary",
  values.primary,
  "edge",
  values.edge,
  values.rotation,
];

export function FieldMap({
  fields,
  counties,
  selectedId,
  countyFilter,
  onSelect,
  className,
}: FieldMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const onSelectRef = useRef(onSelect);
  const [ready, setReady] = useState(false);
  const [imageryFailed, setImageryFailed] = useState(false);
  const [aerialOn, setAerialOn] = useState(false);

  // Latest callback without re-creating the map.
  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  const pilotBounds = ringBounds(counties.map((county) => county.ring));
  const selected = fields.find((field) => field.id === selectedId);
  const imageryState = useFieldImagery(selected?.id);
  const photo = imageryState.status === "ready" ? imageryState.imagery : null;

  function fit(bounds: Bounds, options: { padding: number; maxZoom?: number }) {
    const map = mapRef.current;
    if (!map) return;
    map.fitBounds(
      [
        [bounds[0], bounds[1]],
        [bounds[2], bounds[3]],
      ],
      { ...options, duration: prefersReducedMotion() ? 0 : 900 },
    );
  }

  // Create the map once.
  useEffect(() => {
    let cancelled = false;
    let map: MapLibreMap | undefined;

    async function init() {
      const maplibregl = await import("maplibre-gl");
      if (cancelled || !containerRef.current) return;
      maplibregl.setWorkerUrl(WORKER_URL);
      const colors = readTokens();

      const instance = new maplibregl.Map({
        container: containerRef.current,
        bounds: [
          [pilotBounds[0], pilotBounds[1]],
          [pilotBounds[2], pilotBounds[3]],
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
            "field-polygons": { type: "geojson", data: fieldPolygons(fields) },
            "field-points": { type: "geojson", data: fieldPoints(fields) },
            "selected-polygon": { type: "geojson", data: emptyCollection },
            "selected-point": { type: "geojson", data: emptyCollection },
          },
          layers: [
            {
              id: "backdrop",
              type: "background",
              paint: { "background-color": colors.backdrop },
            },
            { id: "imagery", type: "raster", source: "imagery" },
            {
              id: "counties-line",
              type: "line",
              source: "counties",
              paint: {
                "line-color": colors.white,
                "line-width": 2,
                "line-opacity": 0.85,
              },
            },
            {
              id: "fields-fill",
              type: "fill",
              source: "field-polygons",
              minzoom: OUTLINE_ZOOM,
              paint: {
                "fill-color": kindMatch({
                  primary: colors.primary,
                  rotation: colors.white,
                  edge: colors.edge,
                }),
                "fill-opacity": 0.3,
              },
            },
            {
              id: "fields-line",
              type: "line",
              source: "field-polygons",
              minzoom: OUTLINE_ZOOM,
              paint: { "line-color": colors.white, "line-width": 1.5 },
            },
            {
              id: "field-points",
              type: "circle",
              source: "field-points",
              maxzoom: OUTLINE_ZOOM,
              paint: {
                "circle-radius": 6,
                "circle-color": kindMatch({
                  primary: colors.primary,
                  rotation: colors.rotation,
                  edge: colors.edge,
                }),
                "circle-stroke-width": 2,
                "circle-stroke-color": [
                  "match",
                  ["get", "kind"],
                  "primary",
                  colors.ink,
                  "edge",
                  colors.edgeStroke,
                  colors.rotationStroke,
                ],
              },
            },
            {
              id: "selected-halo",
              type: "circle",
              source: "selected-point",
              maxzoom: OUTLINE_ZOOM,
              paint: {
                "circle-radius": 13,
                "circle-color": "rgba(255,255,255,0)",
                "circle-stroke-width": 3,
                "circle-stroke-color": colors.white,
              },
            },
            {
              id: "selected-casing",
              type: "line",
              source: "selected-polygon",
              minzoom: OUTLINE_ZOOM,
              paint: { "line-color": colors.ink, "line-width": 6 },
            },
            {
              id: "selected-outline",
              type: "line",
              source: "selected-polygon",
              minzoom: OUTLINE_ZOOM,
              paint: { "line-color": colors.white, "line-width": 3 },
            },
          ],
        },
      });

      map = instance;
      instance.addControl(
        new maplibregl.NavigationControl({ showCompass: false }),
        "top-right",
      );

      const clickable = ["field-points", "fields-fill"];
      instance.on("click", clickable, (event) => {
        const id = event.features?.[0]?.properties?.id;
        if (typeof id === "string") onSelectRef.current(id);
      });
      instance.on("mouseenter", clickable, () => {
        instance.getCanvas().style.cursor = "pointer";
      });
      instance.on("mouseleave", clickable, () => {
        instance.getCanvas().style.cursor = "";
      });
      instance.on("error", (event) => {
        if ((event as { sourceId?: string }).sourceId === "imagery")
          setImageryFailed(true);
      });

      mapRef.current = instance;
      instance.once("load", () => {
        if (!cancelled) setReady(true);
      });
    }

    void init();
    return () => {
      cancelled = true;
      map?.remove();
      mapRef.current = null;
      setReady(false);
    };
    // The map is created once; later changes are applied by the effects below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reflect the selected field: update highlight sources, and move the camera on change.
  const previousSelectedId = useRef<string | null>(null);
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !selected) return;

    (map.getSource("selected-polygon") as GeoJSONSource).setData(
      fieldPolygons([selected]),
    );
    (map.getSource("selected-point") as GeoJSONSource).setData(fieldPoints([selected]));

    const isFirstRun = previousSelectedId.current === null;
    const changed = previousSelectedId.current !== selected.id;
    previousSelectedId.current = selected.id;

    // On first load show both counties, unless a shared link points at a specific field.
    if (changed && (!isFirstRun || selected.id !== PRIMARY_FIELD_ID)) {
      fit(ringBounds([selected.ring]), { padding: 90, maxZoom: 15 });
    }
  }, [ready, selected]);

  // County filter: show only that county's fields and frame it.
  const previousFilter = useRef<CountyFilter>("all");
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    const filter =
      countyFilter === "all"
        ? null
        : (["==", ["get", "county"], countyFilter] as ExpressionSpecification);
    for (const layer of ["fields-fill", "fields-line", "field-points"])
      map.setFilter(layer, filter);

    if (previousFilter.current !== countyFilter) {
      const rings =
        countyFilter === "all"
          ? counties.map((county) => county.ring)
          : counties
              .filter((county) => county.county === countyFilter)
              .map((county) => county.ring);
      fit(ringBounds(rings), { padding: 24 });
      previousFilter.current = countyFilter;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, countyFilter]);

  // The aerial photo (NAIP): laid over the satellite picture, under the outlines, only while switched on.
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !photo || !aerialOn) return;
    const [west, south, east, north] = photo.bounds;
    map.addSource("aerial", {
      type: "image",
      url: imageryImageUrl(photo.field_id),
      coordinates: [
        [west, north],
        [east, north],
        [east, south],
        [west, south],
      ],
    });
    map.addLayer(
      {
        id: "aerial",
        type: "raster",
        source: "aerial",
        paint: { "raster-fade-duration": 0 },
      },
      "counties-line",
    );
    fit([west, south, east, north], { padding: 40, maxZoom: 19 });
    return () => {
      try {
        if (map.getLayer("aerial")) map.removeLayer("aerial");
        if (map.getSource("aerial")) map.removeSource("aerial");
      } catch {
        // The map was already taken down with the page.
      }
    };
  }, [ready, photo, aerialOn]);

  const buttonClass =
    "min-h-11 rounded-full bg-surface/95 px-3.5 py-2 text-sm font-semibold text-ink shadow-card backdrop-blur hover:bg-surface";

  return (
    <div className="flex min-h-0 flex-col gap-3 lg:flex-1">
      <div
        className={cn(
          "relative min-h-0 overflow-hidden rounded-[var(--radius-card)] border border-line",
          className,
        )}
      >
        {/* MapLibre sets its own container to position: relative, so size it through a wrapper. */}
        <div className="absolute inset-0">
          <div
            ref={containerRef}
            role="region"
            aria-label="Map of the demonstration fields in Story and Boone counties. The field list has the same fields."
            className="size-full"
          />

          <div className="pointer-events-none absolute top-3 left-3 flex flex-wrap gap-2">
            <button
              type="button"
              className={cn(buttonClass, "pointer-events-auto")}
              onClick={() =>
                selected && fit(ringBounds([selected.ring]), { padding: 90, maxZoom: 15 })
              }
            >
              Zoom to field
            </button>
            <button
              type="button"
              className={cn(buttonClass, "pointer-events-auto")}
              onClick={() => fit(pilotBounds, { padding: 24 })}
            >
              Show both counties
            </button>
            {photo ? (
              <button
                type="button"
                aria-pressed={aerialOn}
                className={cn(
                  buttonClass,
                  "pointer-events-auto",
                  aerialOn && "bg-forest-700 text-white hover:bg-forest-800",
                )}
                onClick={() => setAerialOn((on) => !on)}
              >
                Aerial photo
              </button>
            ) : null}
          </div>
        </div>

        {photo && aerialOn ? (
          <div
            role="status"
            className="pointer-events-none absolute bottom-9 left-3 max-w-64 space-y-1.5 rounded-xl bg-surface/95 p-3 text-xs text-ink shadow-card"
          >
            <p className="font-semibold">
              Aerial photo, taken {flightLabel(photo.tiles)}
            </p>
            <p className="text-ink-soft">{photo.note}</p>
            {photo.evidence_type in evidenceTypes ? (
              <EvidenceBadge type={photo.evidence_type as EvidenceTypeId} />
            ) : null}
            <p className="text-ink-faint">{photo.attribution}</p>
          </div>
        ) : null}
        {imageryState.status === "error" ? (
          <p
            role="status"
            className="absolute bottom-9 left-3 max-w-52 rounded-xl bg-clay-100 px-3 py-2 text-xs font-medium text-clay-700"
          >
            Aerial photos are not available right now.
          </p>
        ) : null}
        {imageryFailed ? (
          <p
            role="status"
            className="absolute right-3 bottom-9 max-w-52 rounded-xl bg-clay-100 px-3 py-2 text-xs font-medium text-clay-700"
          >
            Satellite imagery could not load. Field outlines still work.
          </p>
        ) : null}
      </div>
      <ul
        aria-label="Map key"
        className="flex flex-wrap gap-x-5 gap-y-2 px-1 text-sm font-medium text-ink-soft"
      >
        <li className="flex items-center gap-2">
          <span
            aria-hidden
            className="size-3 rounded-full border-2 border-forest-950 bg-harvest-500"
          />
          Primary demo field
        </li>
        <li className="flex items-center gap-2">
          <span
            aria-hidden
            className="size-3 rounded-full border-2 border-forest-700 bg-surface"
          />
          Rotation test field
        </li>
        <li className="flex items-center gap-2">
          <span
            aria-hidden
            className="size-3 rounded-full border-2 border-clay-700 bg-clay-100"
          />
          Edge case
        </li>
      </ul>
    </div>
  );
}
