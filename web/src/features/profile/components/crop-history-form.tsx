"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { saveCropHistory } from "@/features/field/actions";
import { cn } from "@/lib/cn";
import { cropChoices, FIRST_YEAR, presets, SEASONS } from "./crop-choices";

/**
 * Where the farmer says what they grew. It is their word, kept as "Your input" and never presented as data, and
 * it does not make the comparison possible by itself: weather and soil are still not prepared for a drawn boundary.
 */
export function CropHistoryForm({
  fieldId,
  initial,
}: {
  fieldId: string;
  initial?: readonly string[];
}) {
  const router = useRouter();
  const [crops, setCrops] = useState<string[]>(() =>
    initial && initial.length === SEASONS ? [...initial] : Array(SEASONS).fill(""),
  );
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const complete = crops.every((crop) => crop !== "");

  function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    startTransition(async () => {
      const result = await saveCropHistory(fieldId, crops);
      if (!result.ok) {
        setError(result.message);
        return;
      }
      router.refresh();
    });
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <fieldset className="space-y-3">
        <legend className="text-[0.9375rem] font-semibold">
          What did you grow each season?
        </legend>
        <p className="text-sm text-ink-soft">
          Pick a quick start, then change any season. We need all {SEASONS} seasons,
          because that is what our rules read.
        </p>
        <div className="flex flex-wrap gap-2">
          {presets.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => setCrops([...preset.crops])}
              className="rounded-full border border-line-strong bg-surface px-3.5 py-2 text-sm font-medium hover:border-forest-600 hover:bg-forest-50"
            >
              {preset.label}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {crops.map((crop, index) => {
            const year = FIRST_YEAR + index;
            return (
              <label key={year} className="flex flex-col gap-1 text-sm">
                <span className="font-mono text-xs text-ink-faint">{year}</span>
                <select
                  value={crop}
                  required
                  onChange={(event) =>
                    setCrops((previous) =>
                      previous.map((c, i) => (i === index ? event.target.value : c)),
                    )
                  }
                  className={cn(
                    "min-h-11 rounded-xl border bg-surface px-3",
                    crop === ""
                      ? "border-line-strong text-ink-faint"
                      : "border-line text-ink",
                  )}
                >
                  <option value="">Choose…</option>
                  {cropChoices.map((choice) => (
                    <option key={choice.value} value={choice.value}>
                      {choice.label}
                    </option>
                  ))}
                </select>
              </label>
            );
          })}
        </div>
      </fieldset>

      {error ? (
        <p
          role="alert"
          className="rounded-2xl bg-clay-100 px-4 py-3 text-sm text-clay-700"
        >
          {error}
        </p>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="submit"
          disabled={!complete || pending}
          className="inline-flex min-h-12 items-center justify-center rounded-full bg-forest-700 px-6 text-base font-semibold text-white transition-colors hover:bg-forest-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {pending ? "Saving…" : "Save what I grew"}
        </button>
        {!complete ? (
          <span className="text-sm text-ink-faint">Choose a crop for every season.</span>
        ) : null}
      </div>
      <p className="text-sm text-ink-soft">
        This is your own account of what was grown. It is kept as your input and is not
        checked against any map or record.
      </p>
    </form>
  );
}
