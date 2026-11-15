import { RotationRibbon } from "@/components/rotation/rotation-ribbon";
import { strategies } from "@/domain/strategies";
import { cn } from "@/lib/cn";
import { comparisonBlocked, feasibilityCopy } from "../labels";
import type { Decision, StrategyAssessment } from "../types";
import { StatusChip } from "./status-chip";

/** Three options side by side (stacked on a phone). No option is marked best. */
export function StrategyCards({ decision }: { decision: Decision }) {
  const blocked = comparisonBlocked(decision);
  return (
    <ol className="grid gap-5 lg:grid-cols-3">
      {decision.strategies.map((assessment) => {
        const strategy = strategies.find((s) => s.id === assessment.strategy_id);
        if (!strategy) return null;
        return (
          <li key={strategy.id}>
            <StrategyCard assessment={assessment} blocked={blocked} />
          </li>
        );
      })}
    </ol>
  );
}

function StrategyCard({
  assessment,
  blocked,
}: {
  assessment: StrategyAssessment;
  blocked: boolean;
}) {
  const strategy = strategies.find((s) => s.id === assessment.strategy_id)!;
  const isBaseline = strategy.id === "A";
  const feasibility = feasibilityCopy[assessment.feasibility];
  const headingId = `strategy-${strategy.id}`;

  return (
    <article
      aria-labelledby={headingId}
      className="flex h-full flex-col gap-5 rounded-[var(--radius-card)] border border-line bg-surface p-6 shadow-card"
    >
      <header>
        <p className="font-mono text-xs font-medium tracking-[0.14em] text-forest-600 uppercase">
          Option {strategy.id} · {strategy.kind}
        </p>
        <h3 id={headingId} className="mt-1 font-display text-xl font-medium sm:text-2xl">
          {strategy.name}
        </h3>
        <p className="mt-1 text-ink-soft">{strategy.summary}</p>
      </header>

      <RotationRibbon strategy={strategy} />

      <div>
        {isBaseline ? (
          <StatusChip tone="neutral" glyph="●">
            Your starting point
          </StatusChip>
        ) : blocked ? (
          <StatusChip tone="stop" glyph="×">
            Not offered for this field
          </StatusChip>
        ) : (
          <StatusChip tone={feasibility.tone} glyph={feasibility.glyph}>
            {feasibility.label}
          </StatusChip>
        )}

        {assessment.findings.length > 0 && !blocked ? (
          <ul className="mt-3 space-y-2 text-[0.9375rem]">
            {assessment.findings.map((finding) => (
              <li key={finding.rule_id}>{finding.condition_text}</li>
            ))}
          </ul>
        ) : null}
      </div>

      <section
        aria-label={`What option ${strategy.id} needs`}
        className="mt-auto border-t border-line pt-4"
      >
        <h4 className="text-sm font-semibold">What it needs</h4>
        <ul
          className={cn("mt-2 list-disc space-y-1.5 pl-5 text-[0.9375rem] text-ink-soft")}
        >
          {assessment.operational_requirements.map((requirement) => (
            <li key={requirement}>{requirement}</li>
          ))}
        </ul>
      </section>
    </article>
  );
}
