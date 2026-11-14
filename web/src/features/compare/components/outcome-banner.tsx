import { cn } from "@/lib/cn";
import { distinctFindings, effectLabel, outcomeCopy } from "../labels";
import type { Decision, DecisionOutcome } from "../types";

const accent: Record<DecisionOutcome, string> = {
  strategy_worth_exploring: "border-forest-600 bg-forest-50",
  qualified_comparison: "border-harvest-500 bg-harvest-100/60",
  abstention: "border-clay-700 bg-clay-100/60",
};

/**
 * The decision, in words: one of the three outcomes the PRD allows (8.3), why, and what held it
 * back. There is no score, no ranking and no winner. The engine's own sentence is kept for advisers.
 */
export function OutcomeBanner({ decision }: { decision: Decision }) {
  const copy = outcomeCopy[decision.outcome];
  const findings = distinctFindings(decision);

  return (
    <section
      aria-labelledby="outcome-title"
      className={cn(
        "rounded-[var(--radius-card)] border-l-8 p-6 sm:p-8",
        accent[decision.outcome],
      )}
    >
      <p className="font-mono text-xs font-medium tracking-[0.14em] text-ink-soft uppercase">
        What we found
      </p>
      <h2
        id="outcome-title"
        className="mt-2 font-display text-3xl leading-tight font-semibold tracking-tight text-balance sm:text-4xl"
      >
        {copy.title}
      </h2>
      <p className="mt-3 max-w-3xl text-lg text-ink-soft">{copy.summary}</p>

      {findings.length > 0 ? (
        <div className="mt-6">
          <h3 className="text-sm font-semibold">What held it back</h3>
          <ul className="mt-2 space-y-2">
            {findings.map((finding) => (
              <li key={finding.rule_id} className="flex gap-3 text-[0.9375rem]">
                <span className="mt-0.5 w-28 shrink-0 font-mono text-xs font-medium text-ink-faint uppercase">
                  {effectLabel[finding.effect]}
                </span>
                <span>{finding.condition_text}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <details className="mt-6 text-sm">
        <summary className="cursor-pointer font-semibold text-forest-700 hover:underline">
          How this was decided
        </summary>
        <div className="mt-3 space-y-3 text-ink-soft">
          <p>
            The decision engine said: <q>{decision.outcome_reason}</q>.
          </p>
          <p>
            Rules version <span className="font-mono">{decision.rules_version}</span>.
            Every rule is a team-proposed guardrail and has not been reviewed by an
            agronomist.
          </p>
          {findings.length > 0 ? (
            <ul className="space-y-3">
              {findings.map((finding) => (
                <li key={finding.rule_id}>
                  <p className="font-mono text-xs text-ink-faint">{finding.rule_id}</p>
                  <p>{finding.rationale}</p>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </details>
    </section>
  );
}
