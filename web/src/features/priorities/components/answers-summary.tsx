import { ButtonLink } from "@/components/ui/button";
import { compareRoute } from "@/lib/routes";
import { serializeAnswers, countAnswered } from "../answers-codec";
import type { Answers } from "../questions";
import { TOTAL_QUESTIONS } from "../questions";

const uses = [
  {
    title: "Manure",
    body: "In the Iowa trial, part of the fertiliser came from manure. With no manure, that comparison may not apply to you.",
  },
  {
    title: "Equipment and buyers",
    body: "Oats, clover and alfalfa need small-grain equipment (or a contractor) and somewhere to use or sell the crop. With no use or buyer for alfalfa, we will not offer the four-year option.",
  },
  {
    title: "Profit",
    body: "We do not guess profit, and we never boil the options down to one score.",
  },
  {
    title: "Priorities",
    body: "They change what we highlight first. Everything stays visible.",
  },
] as const;

/** Progress and the way on first; how the answers are used underneath, for those who want it. */
export function AnswersSummary({
  fieldId,
  answers,
}: {
  fieldId: string;
  answers: Answers;
}) {
  const answered = countAnswered(answers);
  return (
    <aside
      aria-label="Your progress"
      className="space-y-5 rounded-[var(--radius-card)] border border-line bg-surface p-5 shadow-card"
    >
      <div>
        <p className="text-sm font-medium" aria-live="polite">
          {answered} of {TOTAL_QUESTIONS} answered
        </p>
        <div aria-hidden className="mt-2 h-1.5 overflow-hidden rounded-full bg-sunken">
          <div
            className="h-full rounded-full bg-forest-600 transition-[width] duration-300"
            style={{ width: `${(answered / TOTAL_QUESTIONS) * 100}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-ink-faint">
          Unanswered questions show as “not provided”. They are never treated as “yes”.
        </p>
        <ButtonLink
          href={compareRoute(fieldId, serializeAnswers(answers))}
          className="mt-4 hidden min-h-11 w-full text-sm font-medium lg:inline-flex"
        >
          Compare strategies
        </ButtonLink>
      </div>

      <details className="group border-t border-line pt-3">
        <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between text-sm font-medium text-forest-700 [&::-webkit-details-marker]:hidden">
          How your answers are used
          <span aria-hidden className="text-lg leading-none group-open:hidden">
            +
          </span>
          <span aria-hidden className="hidden text-lg leading-none group-open:inline">
            −
          </span>
        </summary>
        <dl className="mt-2 space-y-3">
          {uses.map((use) => (
            <div key={use.title}>
              <dt className="text-[0.8125rem] font-medium">{use.title}</dt>
              <dd className="mt-0.5 text-[0.8125rem] leading-relaxed text-ink-soft">
                {use.body}
              </dd>
            </div>
          ))}
        </dl>
      </details>
    </aside>
  );
}
