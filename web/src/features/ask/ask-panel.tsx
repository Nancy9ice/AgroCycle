"use client";

import { useActionState, useRef } from "react";
import { cn } from "@/lib/cn";
import type { AskResult } from "./actions";

interface AskPanelProps {
  /** "analysis" uses POST /analyses/{id}/ask; "field" uses POST /fields/{id}/ask */
  contextType: "analysis" | "field";
  contextId: string;
  action: (prev: AskResult | null, formData: FormData) => Promise<AskResult>;
}

const EXAMPLE_QUESTIONS = [
  "Why does it say this about the 4-year rotation?",
  "What does the soil data say about adding alfalfa?",
  "What would I need to know to get a clearer answer?",
];

export function AskPanel({ contextType, contextId, action }: AskPanelProps) {
  const [result, dispatch, isPending] = useActionState(action, null);
  const formRef = useRef<HTMLFormElement>(null);

  function fillExample(q: string) {
    const textarea = formRef.current?.querySelector("textarea");
    if (textarea) {
      textarea.value = q;
      textarea.focus();
    }
  }

  return (
    <section
      aria-labelledby="ask-title"
      className="mt-14 rounded-[var(--radius-card)] border border-line bg-surface p-6 shadow-[var(--shadow-card)] sm:p-8"
    >
      <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
        <h2 id="ask-title" className="font-display text-2xl font-semibold tracking-tight">
          Ask about these results
        </h2>
        <span className="text-xs font-medium tracking-wide text-orbit-700 uppercase">
          AI explanation — not a recommendation
        </span>
      </div>

      <p className="mt-2 max-w-2xl text-sm text-ink-soft">
        Ask a question about what the numbers mean. The AI only sees this result — it
        cannot access your farm, the internet, or any other data.
      </p>

      <form ref={formRef} action={dispatch} className="mt-6 space-y-4">
        {/* Hidden fields carry context */}
        <input type="hidden" name="contextId" value={contextId} />

        <div>
          <label htmlFor="ask-question" className="sr-only">
            Your question
          </label>
          <textarea
            id="ask-question"
            name="question"
            rows={3}
            placeholder="e.g. Why does it say this about the 4-year rotation?"
            className="w-full resize-none rounded-xl border border-line bg-paper px-4 py-3 text-sm text-ink placeholder:text-ink-faint focus:border-forest-600 focus:ring-2 focus:ring-forest-200 focus:outline-none"
          />
        </div>

        {/* Example questions */}
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => fillExample(q)}
              className="min-h-11 rounded-full border border-line px-4 py-1 text-left text-sm text-ink-soft transition-colors hover:border-forest-600 hover:text-forest-700"
            >
              {q}
            </button>
          ))}
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          {/* Audience toggle */}
          <AudienceToggle />

          <button
            type="submit"
            disabled={isPending}
            className={cn(
              "inline-flex min-h-11 items-center justify-center rounded-full px-6 text-sm font-semibold transition-colors",
              isPending
                ? "cursor-wait bg-forest-200 text-forest-700"
                : "bg-forest-700 text-white hover:bg-forest-800 active:bg-forest-950",
            )}
          >
            {isPending ? "Thinking…" : "Ask"}
          </button>
        </div>
      </form>

      {/* Answer */}
      {result !== null && (
        <div className="mt-6 border-t border-line pt-6">
          {result.error ? (
            <p className="text-sm text-clay-700">{result.error}</p>
          ) : result.refused ? (
            <div className="rounded-xl border border-harvest-100 bg-harvest-100 px-4 py-3">
              <p className="text-sm font-medium text-harvest-700">Out of scope</p>
              <p className="mt-1 text-sm text-ink-soft">{result.answer}</p>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm leading-relaxed whitespace-pre-line text-ink">
                {result.answer}
              </p>
              {result.citations.length > 0 && (
                <div>
                  <p className="font-mono text-xs font-medium tracking-wide text-ink-faint uppercase">
                    Based on
                  </p>
                  <ul className="mt-1 flex flex-wrap gap-2">
                    {result.citations.map((c) => (
                      <li
                        key={c}
                        className="rounded-full border border-orbit-100 bg-orbit-100 px-3 py-0.5 font-mono text-xs text-orbit-700"
                      >
                        {c}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <p className="text-xs text-ink-faint">
                This explanation is generated from the data already on this page. It is
                not advice and does not replace agronomist judgement.
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function AudienceToggle() {
  return (
    <fieldset>
      <legend className="sr-only">Explanation style</legend>
      <div className="flex overflow-hidden rounded-full border border-line text-sm">
        {(
          [
            { value: "farmer", label: "Plain language" },
            { value: "adviser", label: "Technical" },
          ] as const
        ).map(({ value, label }, i) => (
          <label
            key={value}
            className={cn(
              "flex cursor-pointer items-center px-4 py-1.5 transition-colors has-[:checked]:bg-forest-700 has-[:checked]:text-white",
              i === 0 ? "" : "border-l border-line",
            )}
          >
            <input
              type="radio"
              name="audience"
              value={value}
              defaultChecked={value === "farmer"}
              className="sr-only"
            />
            {label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
