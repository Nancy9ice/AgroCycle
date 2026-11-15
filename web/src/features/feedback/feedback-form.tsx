"use client";

import { useState, useTransition } from "react";
import { cn } from "@/lib/cn";
import { sendFeedback } from "./actions";
import {
  MAX_MISSING,
  emptyDraft,
  problem,
  roles,
  wouldUseChoices,
  type FeedbackDraft,
} from "./payload";

const scale = [1, 2, 3, 4, 5] as const;

/** The feedback form (spec 5.3). Skipped optional answers are sent as "not provided", never as "no". */
export function FeedbackForm({
  fieldId,
  analysisId,
}: {
  fieldId?: string;
  analysisId?: string;
}) {
  const [draft, setDraft] = useState<FeedbackDraft>(() =>
    emptyDraft(fieldId, analysisId),
  );
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<{ message: string; iowaNote: string } | null>(null);
  const [pending, startTransition] = useTransition();
  const set = <K extends keyof FeedbackDraft>(key: K, value: FeedbackDraft[K]) =>
    setDraft((previous) => ({ ...previous, [key]: value }));

  function submit(event: React.FormEvent) {
    event.preventDefault();
    const invalid = problem(draft);
    if (invalid) {
      setError(invalid);
      return;
    }
    setError(null);
    startTransition(async () => {
      const result = await sendFeedback(draft);
      if (result.ok) setDone({ message: result.message, iowaNote: result.iowaNote });
      else setError(result.message);
    });
  }

  if (done) {
    return (
      <div
        role="status"
        className="rounded-[var(--radius-card)] border border-forest-600 bg-forest-50 p-6"
      >
        <h2 className="font-display text-xl font-semibold">{done.message}</h2>
        <p className="mt-2 max-w-2xl text-[0.9375rem] text-ink-soft">{done.iowaNote}</p>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="space-y-8" noValidate>
      <fieldset className="space-y-2">
        <legend className="font-semibold">Who are you? (required)</legend>
        <div className="flex flex-wrap gap-2">
          {roles.map((role) => (
            <label
              key={role.value}
              className={cn(
                "inline-flex min-h-11 cursor-pointer items-center rounded-full border px-4 text-[0.9375rem] font-medium",
                draft.role === role.value
                  ? "border-forest-700 bg-forest-700 text-white"
                  : "border-line-strong bg-surface hover:border-forest-600",
              )}
            >
              <input
                type="radio"
                name="role"
                value={role.value}
                checked={draft.role === role.value}
                onChange={() => set("role", role.value)}
                className="sr-only"
              />
              {role.label}
            </label>
          ))}
        </div>
      </fieldset>

      <label className="block space-y-2">
        <span className="font-semibold">
          Where are you farming or working? (optional)
        </span>
        <input
          type="text"
          maxLength={120}
          value={draft.farmingContext}
          onChange={(event) => set("farmingContext", event.target.value)}
          placeholder="For example: a farmer in Nigeria, or an Iowa adviser"
          className="min-h-11 w-full max-w-xl rounded-xl border border-line-strong bg-surface px-3"
        />
        <span className="block text-sm text-ink-soft">
          This keeps feedback from Iowa separate from feedback from elsewhere. Both are
          useful, in different ways.
        </span>
      </label>

      <Rating
        name="usefulness"
        label="How useful was it? (required)"
        low="Not useful"
        high="Very useful"
        value={draft.usefulness}
        onChange={(value) => set("usefulness", value)}
      />
      <Rating
        name="clarity"
        label="How clear was it? (required)"
        low="Confusing"
        high="Very clear"
        value={draft.clarity}
        onChange={(value) => set("clarity", value)}
      />

      <label className="block space-y-2">
        <span className="font-semibold">
          What was missing, or hard to understand? (optional)
        </span>
        <textarea
          rows={4}
          maxLength={MAX_MISSING}
          value={draft.whatWasMissing}
          onChange={(event) => set("whatWasMissing", event.target.value)}
          className="w-full max-w-2xl rounded-xl border border-line-strong bg-surface px-3 py-2"
        />
        <span className="block text-sm text-ink-faint">
          {draft.whatWasMissing.length} of {MAX_MISSING}
        </span>
      </label>

      <fieldset className="space-y-2">
        <legend className="font-semibold">
          Would you use it on your own farm? (optional)
        </legend>
        <div className="flex flex-wrap gap-2">
          {wouldUseChoices.map((choice) => (
            <label
              key={choice.value}
              className={cn(
                "inline-flex min-h-11 cursor-pointer items-center rounded-full border px-4 text-[0.9375rem] font-medium",
                draft.wouldUse === choice.value
                  ? "border-forest-700 bg-forest-700 text-white"
                  : "border-line-strong bg-surface hover:border-forest-600",
              )}
            >
              <input
                type="radio"
                name="wouldUse"
                value={choice.value}
                checked={draft.wouldUse === choice.value}
                onChange={() => set("wouldUse", choice.value)}
                className="sr-only"
              />
              {choice.label}
            </label>
          ))}
          {draft.wouldUse !== "" ? (
            <button
              type="button"
              onClick={() => set("wouldUse", "")}
              className="min-h-11 rounded-full px-3 text-sm text-ink-soft underline underline-offset-4"
            >
              Clear
            </button>
          ) : null}
        </div>
      </fieldset>

      <fieldset className="space-y-2">
        <legend className="font-semibold">Can we contact you? (optional)</legend>
        <input
          type="text"
          maxLength={200}
          value={draft.contact}
          onChange={(event) => set("contact", event.target.value)}
          aria-label="Your email or phone"
          placeholder="Email or phone"
          className="min-h-11 w-full max-w-xl rounded-xl border border-line-strong bg-surface px-3"
        />
        <label className="flex max-w-2xl items-start gap-3 text-[0.9375rem]">
          <input
            type="checkbox"
            checked={draft.consent}
            onChange={(event) => set("consent", event.target.checked)}
            className="mt-1 size-5"
          />
          <span>
            I agree that the AgroCycle team may keep these contact details and use them to
            follow up on this feedback. Without this box ticked, nothing you type above is
            kept.
          </span>
        </label>
      </fieldset>

      {fieldId || analysisId ? (
        <p className="text-sm text-ink-soft">
          This feedback will be linked to the field and comparison you were looking at, so
          we can see what you saw.
        </p>
      ) : null}

      {error ? (
        <p
          role="alert"
          className="rounded-2xl bg-clay-100 px-4 py-3 text-[0.9375rem] text-clay-700"
        >
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={pending}
        className="inline-flex min-h-12 items-center justify-center rounded-full bg-forest-700 px-8 text-base font-semibold text-white transition-colors hover:bg-forest-800 disabled:opacity-60"
      >
        {pending ? "Sending…" : "Send feedback"}
      </button>
    </form>
  );
}

function Rating({
  name,
  label,
  low,
  high,
  value,
  onChange,
}: {
  name: string;
  label: string;
  low: string;
  high: string;
  value: number | null;
  onChange: (value: number) => void;
}) {
  return (
    <fieldset className="space-y-2">
      <legend className="font-semibold">{label}</legend>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-ink-soft">{low}</span>
        {scale.map((n) => (
          <label
            key={n}
            className={cn(
              "inline-flex size-11 cursor-pointer items-center justify-center rounded-full border font-mono font-semibold",
              value === n
                ? "border-forest-700 bg-forest-700 text-white"
                : "border-line-strong bg-surface hover:border-forest-600",
            )}
          >
            <input
              type="radio"
              name={name}
              value={n}
              checked={value === n}
              onChange={() => onChange(n)}
              className="sr-only"
            />
            {n}
          </label>
        ))}
        <span className="text-sm text-ink-soft">{high}</span>
      </div>
    </fieldset>
  );
}
