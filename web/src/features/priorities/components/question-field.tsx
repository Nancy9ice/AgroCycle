"use client";

import { useId } from "react";
import { cn } from "@/lib/cn";
import type { Question } from "../questions";

interface QuestionFieldProps {
  question: Question;
  value: string | undefined;
  onChange: (value: string | undefined) => void;
}

/**
 * One optional question as a native radio group: arrow keys move between options, and
 * "Clear answer" returns it to unanswered. Constraints say why they are asked and whether
 * the comparison reads them yet.
 */
export function QuestionField({ question, value, onChange }: QuestionFieldProps) {
  const name = useId();
  const isConstraint = question.group === "constraint";
  const usedByEngine = "engineKey" in question;

  return (
    <fieldset className="flex h-full flex-col gap-2.5 rounded-2xl border border-line bg-surface p-4">
      <legend className="float-left mb-2.5 w-full text-[0.9375rem] leading-snug font-medium">
        {question.label}
      </legend>

      {question.why ? (
        <p className="clear-both text-[0.8125rem] leading-relaxed text-ink-soft">
          {question.why}
        </p>
      ) : (
        <span className="clear-both" />
      )}

      <div className="clear-both flex flex-wrap gap-2">
        {question.options.map((option) => (
          <label key={option.value} className="cursor-pointer">
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
              className="peer sr-only"
            />
            <span
              className={cn(
                "inline-flex min-h-10 items-center rounded-full border border-line-strong bg-surface px-3.5 text-sm font-medium transition-colors",
                "hover:border-forest-600 hover:bg-forest-50",
                "peer-checked:border-forest-700 peer-checked:bg-forest-700 peer-checked:text-white",
                "peer-focus-visible:outline-3 peer-focus-visible:outline-offset-3 peer-focus-visible:outline-orbit-700",
              )}
            >
              {option.label}
            </span>
          </label>
        ))}
      </div>

      <div className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-1">
        {isConstraint ? (
          <span
            className={cn(
              "rounded-full px-2.5 py-0.5 font-mono text-[0.6875rem]",
              usedByEngine ? "bg-forest-100 text-forest-800" : "bg-sunken text-ink-faint",
            )}
          >
            {usedByEngine ? "Used in the comparison" : "Recorded for your adviser"}
          </span>
        ) : (
          <span className="rounded-full bg-sunken px-2.5 py-0.5 font-mono text-[0.6875rem] text-ink-faint">
            Changes what we highlight
          </span>
        )}
        {value !== undefined ? (
          <button
            type="button"
            onClick={() => onChange(undefined)}
            className="min-h-10 rounded-full px-3 text-[0.8125rem] font-medium text-forest-700 hover:bg-forest-100"
          >
            Clear answer<span className="sr-only">: {question.label}</span>
          </button>
        ) : null}
      </div>
    </fieldset>
  );
}
