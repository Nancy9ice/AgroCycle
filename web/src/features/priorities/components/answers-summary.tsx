import { ButtonLink } from "@/components/ui/button";
import { compareRoute, profileRoute } from "@/lib/routes";
import { serializeAnswers } from "../answers-codec";
import type { Answers } from "../questions";
import { TOTAL_QUESTIONS } from "../questions";
import { countAnswered } from "../answers-codec";

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

/** Progress, how the answers are used, and the way on. */
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
      aria-labelledby="how-used-title"
      className="space-y-6 rounded-[var(--radius-card)] border border-line bg-surface p-6 shadow-card"
    >
      <div>
        <h2 id="how-used-title" className="font-display text-xl font-semibold">
          How your answers are used
        </h2>
        <dl className="mt-4 space-y-4">
          {uses.map((use) => (
            <div key={use.title}>
              <dt className="text-sm font-semibold">{use.title}</dt>
              <dd className="mt-0.5 text-[0.9375rem] text-ink-soft">{use.body}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="border-t border-line pt-5">
        <p className="font-semibold" aria-live="polite">
          Answered so far: {answered} of {TOTAL_QUESTIONS}
        </p>
        <p className="mt-1 text-sm text-ink-faint">
          Unanswered questions show as “not provided” in the comparison. They are never
          treated as “yes”.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <ButtonLink href={compareRoute(fieldId, serializeAnswers(answers))}>
          Compare strategies
        </ButtonLink>
        <ButtonLink href={profileRoute(fieldId)} variant="secondary">
          Back to profile
        </ButtonLink>
      </div>
    </aside>
  );
}
