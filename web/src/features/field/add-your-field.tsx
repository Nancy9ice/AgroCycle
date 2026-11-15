"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ButtonLink } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import { demoFieldsRoute } from "@/lib/routes";
import {
  MIN_CORNERS,
  checkDraftBoundary,
  describeArea,
  locateInPilot,
  locationErrorMessage,
} from "./boundary-draft";
import { counties } from "./data";
import { DrawMap, type DrawMapApi, type MapFocus } from "./draw-map";
import type { LonLat } from "./types";

type LocationState =
  | { status: "idle" }
  | { status: "asking" }
  | { status: "inside"; county: string; approximate: boolean }
  | { status: "outside" }
  | { status: "failed"; message: string };

const control =
  "inline-flex min-h-12 items-center justify-center rounded-full border px-5 text-[0.9375rem] font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50";
const quiet = `${control} border-line-strong bg-surface text-ink hover:border-forest-600 hover:bg-forest-50 disabled:hover:border-line-strong disabled:hover:bg-surface`;
const solid = `${control} border-forest-700 bg-forest-700 text-white hover:bg-forest-800 disabled:hover:bg-forest-700`;

const plural = (count: number, word: string) =>
  `${count} ${word}${count === 1 ? "" : "s"}`;

/**
 * Step 1 for a farmer's own field: find the field, tap its corners, check the boundary.
 *
 * The boundary and the position stay in this browser. The API can validate a boundary but does not
 * yet store one or prepare any data for it, so a valid boundary ends in an honest "not yet" and a way
 * to see the product on a demo field. It never shows another field's numbers as the farmer's.
 */
export function AddYourField() {
  const [corners, setCorners] = useState<LonLat[]>([]);
  const [finished, setFinished] = useState(false);
  const [here, setHere] = useState<LonLat | null>(null);
  const [focus, setFocus] = useState<MapFocus | null>(null);
  const [location, setLocation] = useState<LocationState>({ status: "idle" });
  const apiRef = useRef<DrawMapApi | null>(null);
  const focusCount = useRef(0);
  const resultRef = useRef<HTMLElement>(null);

  const addCorner = useCallback((corner: LonLat) => {
    setCorners((previous) => [...previous, corner]);
  }, []);

  const handleReady = useCallback((api: DrawMapApi) => {
    apiRef.current = api;
  }, []);

  const addAtCross = () => {
    const centre = apiRef.current?.getCentre();
    if (centre) addCorner(centre);
  };

  const useMyLocation = () => {
    if (typeof navigator === "undefined" || !("geolocation" in navigator)) {
      setLocation({ status: "failed", message: locationErrorMessage("unsupported") });
      return;
    }
    setLocation({ status: "asking" });
    navigator.geolocation.getCurrentPosition(
      (result) => {
        const position: LonLat = [result.coords.longitude, result.coords.latitude];
        setHere(position);
        const outcome = locateInPilot(position, result.coords.accuracy, counties);
        if (outcome.kind === "outside") {
          setLocation({ status: "outside" });
          return;
        }
        focusCount.current += 1;
        setFocus({ position, zoom: 16, nonce: focusCount.current });
        setLocation({
          status: "inside",
          county: outcome.county,
          approximate: outcome.approximate,
        });
      },
      (error) =>
        setLocation({ status: "failed", message: locationErrorMessage(error.code) }),
      { enableHighAccuracy: true, timeout: 15_000, maximumAge: 60_000 },
    );
  };

  const report = finished ? checkDraftBoundary(corners, counties) : null;

  // Bring the result into view and announce it, so nobody has to hunt for it under the map.
  useEffect(() => {
    if (finished) resultRef.current?.focus();
  }, [finished]);
  const canFinish = corners.length >= MIN_CORNERS;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,24rem)] lg:gap-10">
      <div className="space-y-4">
        <DrawMap
          counties={counties}
          corners={corners}
          here={here}
          focus={focus}
          drawing={!finished}
          onAddCorner={addCorner}
          onReady={handleReady}
          className="h-[min(26rem,62dvh)] sm:h-[32rem] lg:h-[36rem]"
        />

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={useMyLocation}
            disabled={location.status === "asking"}
            className={solid}
          >
            {location.status === "asking" ? "Finding you…" : "Use my location"}
          </button>
          <button
            type="button"
            onClick={addAtCross}
            disabled={finished}
            className={quiet}
          >
            Add corner at the cross
          </button>
          <button
            type="button"
            onClick={() => setCorners((previous) => previous.slice(0, -1))}
            disabled={finished || corners.length === 0}
            className={quiet}
          >
            Undo last corner
          </button>
          <button
            type="button"
            onClick={() => {
              setCorners([]);
              setFinished(false);
            }}
            disabled={corners.length === 0}
            className={quiet}
          >
            Start again
          </button>
        </div>

        <p aria-live="polite" className="text-[0.9375rem] text-ink-soft">
          {location.status === "inside" ? (
            <>
              You are in {location.county} County.{" "}
              {location.approximate
                ? "Your phone gave a rough position, so check the map is on your field. "
                : ""}
              Tap the corners of your field.
            </>
          ) : null}
          {location.status === "outside" ? (
            <>
              You are outside Story and Boone counties, Iowa, the only area we cover for
              now. You can still try a demo field to see how the comparison works.
            </>
          ) : null}
          {location.status === "failed" ? location.message : null}
          {location.status === "idle" || location.status === "asking"
            ? "Your location stays on your device. We do not send it anywhere."
            : null}
        </p>
      </div>

      <div className="flex flex-col gap-5">
        <ol className="order-last space-y-3 rounded-[var(--radius-card)] border border-line bg-surface p-5 text-[0.9375rem] shadow-card lg:order-first">
          {[
            "Find your field: press “Use my location”, or move the map.",
            "Tap each corner of the field, one after another. Or move the map so the cross sits on a corner and press “Add corner at the cross”.",
            "Press “Check my boundary” when every corner is marked.",
          ].map((text, index) => (
            <li key={text} className="flex gap-3">
              <span
                aria-hidden
                className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-forest-100 font-mono text-xs font-semibold text-forest-800"
              >
                {index + 1}
              </span>
              <span>{text}</span>
            </li>
          ))}
        </ol>

        <div
          aria-live="polite"
          className="rounded-[var(--radius-card)] border border-line bg-surface p-5 shadow-card"
        >
          <p className="font-semibold">{plural(corners.length, "corner")} marked</p>
          {!finished ? (
            <button
              type="button"
              onClick={() => setFinished(true)}
              disabled={!canFinish}
              className={cn(solid, "mt-3 w-full")}
            >
              Check my boundary
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setFinished(false)}
              className={cn(quiet, "mt-3 w-full")}
            >
              Change the corners
            </button>
          )}
          {!canFinish && !finished ? (
            <p className="mt-2 text-sm text-ink-faint">
              A field needs at least {MIN_CORNERS} corners.
            </p>
          ) : null}
        </div>

        {report ? (
          <section
            ref={resultRef}
            tabIndex={-1}
            aria-labelledby="own-result-title"
            className={cn(
              "scroll-mt-24 space-y-3 rounded-[var(--radius-card)] border p-5 outline-none",
              report.valid
                ? "border-forest-600 bg-forest-50"
                : "border-clay-700 bg-clay-100",
            )}
          >
            <h2 id="own-result-title" className="font-semibold">
              {report.valid ? "Your boundary looks good" : "This boundary needs a change"}
            </h2>
            {report.valid ? (
              <>
                <p className="text-[0.9375rem]">
                  About {describeArea(report.areaHa ?? 0)} in {report.county} County.
                </p>
                <p className="text-[0.9375rem] text-ink-soft">
                  <strong className="text-ink">
                    We cannot compare your own field yet.
                  </strong>{" "}
                  The crop history, soil and weather for a new boundary still have to be
                  prepared, and we will not show another field’s numbers as yours. See how
                  the comparison works on a demo field meanwhile.
                </p>
                <ButtonLink href={demoFieldsRoute} className="w-full">
                  Try a demo field
                </ButtonLink>
                <p className="text-sm text-ink-faint">
                  Your boundary stayed on this device. Nothing was saved.
                </p>
              </>
            ) : (
              <ul className="list-disc space-y-1 pl-5 text-[0.9375rem]">
                {report.issues.map((issue) => (
                  <li key={issue.code}>{issue.message}</li>
                ))}
              </ul>
            )}
          </section>
        ) : null}

        <p className="order-last text-sm text-ink-faint">
          Uploading a boundary file (for example from your farm software) is not available
          yet.
        </p>
      </div>
    </div>
  );
}
