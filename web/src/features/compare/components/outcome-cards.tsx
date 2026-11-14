import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import { strategies } from "@/domain/strategies";
import { cn } from "@/lib/cn";
import { outcomeStatusCopy } from "../labels";
import { marsdenFigures } from "../marsden-figures";
import type { Decision, OutcomeAssessment } from "../types";
import { StatusChip } from "./status-chip";

interface OutcomeCardsProps {
  decision: Decision;
  /** Outcome ids tied to a high priority, tagged so the person can find them. */
  highlighted: ReadonlySet<string>;
}

/**
 * Every outcome the engine returns, including the ones it withholds or cannot assess: an
 * unavailable dimension is shown as such, never dropped or shown as neutral (PRD 8.2).
 */
export function OutcomeCards({ decision, highlighted }: OutcomeCardsProps) {
  return (
    <ul className="space-y-4">
      {decision.outcomes.map((outcome) => (
        <li key={outcome.outcome_id}>
          <OutcomeCard
            outcome={outcome}
            highlighted={highlighted.has(outcome.outcome_id)}
          />
        </li>
      ))}
    </ul>
  );
}

function OutcomeCard({
  outcome,
  highlighted,
}: {
  outcome: OutcomeAssessment;
  highlighted: boolean;
}) {
  const status = outcomeStatusCopy[outcome.status];
  const speakable = outcome.statement !== null;
  const figures = speakable ? marsdenFigures[outcome.outcome_id] : undefined;
  const headingId = `outcome-${outcome.outcome_id}`;
  const reasons = outcome.findings.filter((finding) => finding.effect !== "in_domain");

  return (
    <article
      aria-labelledby={headingId}
      className={cn(
        "rounded-[var(--radius-card)] border bg-surface p-5 sm:p-6",
        highlighted ? "border-forest-600 shadow-card" : "border-line",
      )}
    >
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          {highlighted ? (
            <p className="mb-1 font-mono text-xs font-medium tracking-wide text-forest-600 uppercase">
              You said this matters
            </p>
          ) : null}
          <h3 id={headingId} className="text-lg font-semibold">
            {outcome.label}
          </h3>
        </div>
        <StatusChip tone={status.tone} glyph={status.glyph}>
          {status.label}
        </StatusChip>
      </header>

      {speakable ? (
        <div className="mt-3 space-y-4">
          <p className="max-w-3xl text-[0.9375rem]">{outcome.statement}</p>
          {figures ? <Figures figures={figures} /> : null}
          <div className="flex flex-wrap items-center gap-2 text-sm text-ink-faint">
            {outcome.evidence_type ? (
              <EvidenceBadge type={outcome.evidence_type} />
            ) : null}
            {outcome.source ? <span>{outcome.source}</span> : null}
          </div>
        </div>
      ) : (
        <p className="mt-3 max-w-3xl text-[0.9375rem] text-ink-soft">
          {outcome.claimable
            ? "We are not showing this for your field. Missing information is not treated as good or bad news."
            : "This is not assessed. We have no data that measures it on a field, so we say nothing about it."}
        </p>
      )}

      {reasons.length > 0 ? (
        <ul className="mt-3 space-y-1 text-[0.9375rem]">
          {reasons.map((reason) => (
            <li key={reason.rule_id} className="flex gap-2">
              <span aria-hidden className="text-ink-faint">
                →
              </span>
              <span>{reason.condition_text}</span>
            </li>
          ))}
        </ul>
      ) : null}

      <p className="mt-4 rounded-xl bg-sunken px-4 py-3 text-sm text-ink-soft">
        <span className="font-semibold text-ink">What this does not tell you. </span>
        {outcome.caution}
      </p>
    </article>
  );
}

function Figures({ figures }: { figures: NonNullable<(typeof marsdenFigures)[string]> }) {
  return (
    <div className="rounded-xl border border-line">
      <p className="border-b border-line px-4 py-2 text-xs font-medium text-ink-faint">
        Average over nine years at one Iowa research site, in {figures.unit}
      </p>
      <div className="divide-y divide-line">
        {figures.rows.map((row) => (
          <div key={row.label} className="px-4 py-3">
            <p className="text-[0.9375rem] font-medium">{row.label}</p>
            <ul className="mt-2 grid grid-cols-3 gap-3">
              {strategies.map((strategy) => (
                <li key={strategy.id}>
                  <span className="block font-mono text-xl font-semibold">
                    {row.values[strategy.id]}
                  </span>
                  <span className="block text-xs text-ink-faint">
                    Option {strategy.id}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
