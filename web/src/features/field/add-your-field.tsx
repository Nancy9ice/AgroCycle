"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState, useTransition } from "react";
import { LocateIcon } from "@/components/icons/locate-icon";
import { PlusIcon } from "@/components/icons/plus-icon";
import { ResetIcon } from "@/components/icons/reset-icon";
import { UndoIcon } from "@/components/icons/undo-icon";
import { ButtonLink } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import { demoFieldsRoute, profileRoute } from "@/lib/routes";
import { saveDrawnBoundary } from "./actions";
import {
  MIN_CORNERS,
  checkDraftBoundary,
  describeArea,
  findPosition,
  locateInPilot,
  locationErrorMessage,
  ringFromCorners,
} from "./boundary-draft";
import { DrawMap, type DrawMapApi, type MapFocus } from "./draw-map";
import type { County, LonLat } from "./types";

type LocationState =
  | { status: "idle" }
  | { status: "asking" }
  | { status: "inside"; county: string; approximate: boolean }
  | { status: "outside" }
  | { status: "failed"; message: string };

/** Buttons in the toolbar under the map. */
const toolBase =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-full border px-4 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40 sm:px-5";
const tool = `${toolBase} border-line-strong bg-surface text-ink hover:border-forest-600 hover:bg-forest-50 disabled:hover:border-line-strong disabled:hover:bg-surface`;
const toolSolid = `${toolBase} border-forest-700 bg-forest-700 text-white hover:bg-forest-800 disabled:hover:bg-forest-700`;

const plural = (count: number, word: string) =>
  `${count} ${word}${count === 1 ? "" : "s"}`;

/**
 * Step 1 for a farmer's own field: find the field, tap its corners, check the boundary.
 *
 * The position and the boundary stay in this browser until the farmer chooses to continue; only then is the
 * boundary sent to be kept. Nothing is prepared for a drawn boundary, so its profile shows what is missing and
 * the comparison says "not enough evidence". It never shows another field's numbers as the farmer's.
 */
export function AddYourField({ counties }: { counties: readonly County[] }) {
  const router = useRouter();
  const [saving, startSaving] = useTransition();
  const [saveError, setSaveError] = useState<string | null>(null);
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
    findPosition(
      navigator.geolocation,
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
    );
  };

  const report = finished ? checkDraftBoundary(corners, counties) : null;

  /** Keep the boundary on the server (only now) and carry on to its profile. */
  const carryOn = () => {
    setSaveError(null);
    startSaving(async () => {
      const result = await saveDrawnBoundary(ringFromCorners(corners));
      if (!result.ok) {
        setSaveError(result.message);
        return;
      }
      router.push(profileRoute(result.fieldId));
    });
  };

  // Bring the result into view and announce it, so nobody has to hunt for it under the map.
  useEffect(() => {
    if (finished) resultRef.current?.focus();
  }, [finished]);

  const canFinish = corners.length >= MIN_CORNERS;
  const remaining = MIN_CORNERS - corners.length;

  // One line that always says what to do next. A location message wins until the first corner is placed.
  const locationMessage =
    location.status === "inside"
      ? `You are in ${location.county} County. ${
          location.approximate
            ? "Your phone gave a rough position, so check the map is on your field. "
            : ""
        }Tap the corners of your field.`
      : location.status === "outside"
        ? "You are outside Story and Boone counties, Iowa, the only area we cover for now. You can still try a demo field."
        : location.status === "failed"
          ? location.message
          : null;
  const stepHint =
    corners.length === 0
      ? "Tap the map to place the first corner of your field."
      : canFinish
        ? `${plural(corners.length, "corner")} placed. Check your boundary when the shape is complete.`
        : `${plural(corners.length, "corner")} placed. Add ${remaining} more.`;
  const hint = finished
    ? null
    : corners.length === 0 && locationMessage
      ? locationMessage
      : stepHint;

  return (
    <div className="space-y-4">
      <div className="relative">
        <DrawMap
          counties={counties}
          corners={corners}
          here={here}
          focus={focus}
          drawing={!finished}
          onAddCorner={addCorner}
          onReady={handleReady}
          className="h-[min(40rem,calc(100dvh-22rem))] min-h-[22rem]"
        />
      </div>

      {/* Controls live under the map, so nothing covers the satellite picture you are tracing. */}
      <div className="space-y-3">
        {hint ? (
          <p aria-live="polite" className="text-sm text-ink sm:text-[0.9375rem]">
            {hint}
          </p>
        ) : null}
        <div
          role="toolbar"
          aria-label="Draw your field"
          className="flex flex-wrap items-center gap-2"
        >
          <button
            type="button"
            onClick={useMyLocation}
            disabled={location.status === "asking"}
            className={tool}
          >
            <LocateIcon className="size-5 text-forest-700" />
            {location.status === "asking" ? "Finding you…" : "Use my location"}
          </button>
          {!finished ? (
            <>
              <button
                type="button"
                onClick={addAtCross}
                aria-label="Add corner at the cross"
                className={toolSolid}
              >
                <PlusIcon className="size-5" />
                Add corner
              </button>
              <button
                type="button"
                onClick={() => setCorners((previous) => previous.slice(0, -1))}
                disabled={corners.length === 0}
                aria-label="Undo last corner"
                className={tool}
              >
                <UndoIcon className="size-5" />
                Undo
              </button>
              <button
                type="button"
                onClick={() => {
                  setCorners([]);
                  setFinished(false);
                }}
                disabled={corners.length === 0}
                aria-label="Start again"
                className={tool}
              >
                <ResetIcon className="size-5" />
                Start again
              </button>
              <button
                type="button"
                onClick={() => setFinished(true)}
                disabled={!canFinish}
                className={cn(toolSolid, "w-full sm:ml-auto sm:w-auto")}
              >
                Check my boundary
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => setFinished(false)}
                className={toolSolid}
              >
                Change the corners
              </button>
              <button
                type="button"
                onClick={() => {
                  setCorners([]);
                  setFinished(false);
                }}
                className={tool}
              >
                <ResetIcon className="size-5" />
                Start again
              </button>
            </>
          )}
        </div>
      </div>

      <p className="text-xs text-ink-faint sm:text-sm">
        Your location never leaves this device. Your boundary stays here until you choose
        to continue, and then we keep it so you can come back to it.
        <span className="hidden sm:inline">
          {" "}
          Uploading a boundary file from farm software is not available yet.
        </span>
      </p>

      {report ? (
        <section
          ref={resultRef}
          tabIndex={-1}
          aria-labelledby="own-result-title"
          className={cn(
            "scroll-mt-24 rounded-[var(--radius-card)] border p-5 outline-none sm:p-6",
            report.valid
              ? "border-forest-600 bg-forest-50"
              : "border-clay-700 bg-clay-100",
          )}
        >
          <h2 id="own-result-title" className="font-display text-xl font-semibold">
            {report.valid ? "Your boundary looks good" : "This boundary needs a change"}
          </h2>
          {report.valid ? (
            <div className="mt-2 grid gap-5 md:grid-cols-[1fr_auto] md:items-center">
              <div className="space-y-2 text-[0.9375rem]">
                <p>
                  About {describeArea(report.areaHa ?? 0)} in {report.county} County.
                </p>
                <p className="text-ink-soft">
                  <strong className="text-ink">
                    We have not prepared any data for your own field yet.
                  </strong>{" "}
                  You can carry on: you will see what is missing, and you can tell us what
                  you grew. The comparison will say “not enough evidence” and name what is
                  still needed, because we will not show another field’s numbers as yours.
                  Nothing is saved until you continue.
                </p>
                {saveError ? (
                  <p role="alert" className="text-clay-700">
                    {saveError}
                  </p>
                ) : null}
              </div>
              <div className="flex flex-col gap-2 sm:flex-row md:flex-col">
                <button
                  type="button"
                  onClick={carryOn}
                  disabled={saving}
                  className="inline-flex min-h-12 items-center justify-center rounded-full bg-forest-700 px-6 text-base font-semibold text-white transition-colors hover:bg-forest-800 disabled:opacity-60"
                >
                  {saving ? "Saving…" : "Continue with this boundary"}
                </button>
                <ButtonLink href={demoFieldsRoute} variant="secondary">
                  Try a demo field
                </ButtonLink>
              </div>
            </div>
          ) : (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-[0.9375rem]">
              {report.issues.map((issue) => (
                <li key={issue.code}>{issue.message}</li>
              ))}
            </ul>
          )}
        </section>
      ) : null}
    </div>
  );
}
