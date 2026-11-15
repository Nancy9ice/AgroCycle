"use client";

import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import { evidenceTypes } from "@/domain/evidence";
import type { Indicator, SectionStatus } from "../types";
import { useProfileUi } from "./profile-ui";
import { ProvenanceButton } from "./provenance-button";

/** One headline number with its meaning, evidence label and a way to see where it came from. */
export function IndicatorCard({
  indicator,
  status,
}: {
  indicator: Indicator;
  status: SectionStatus;
}) {
  const { view } = useProfileUi();
  const { provenance } = indicator;
  const isSample = status === "sample";

  return (
    <article className="flex flex-col rounded-[var(--radius-card)] border border-line bg-surface p-5">
      <h3 className="text-sm font-medium text-ink-soft">{indicator.label}</h3>
      <p className="mt-2 font-display text-3xl leading-tight font-semibold">
        {indicator.value}
      </p>
      <p className="mt-2 flex-1 text-[0.9375rem] text-ink-soft">{indicator.context}</p>

      <div className="mt-4 space-y-2 border-t border-line pt-3">
        <EvidenceBadge type={provenance.technical.evidenceType} />
        <p className="text-sm text-ink-faint">
          {evidenceTypes[provenance.technical.evidenceType].plain}
        </p>
        {view === "detailed" ? (
          <p className="font-mono text-xs break-words text-ink-faint">
            {provenance.technical.scale} · {provenance.technical.variable} ·{" "}
            {provenance.technical.indicatorId}
          </p>
        ) : null}
        <ProvenanceButton provenance={provenance} isSample={isSample} className="-ml-3" />
      </div>
    </article>
  );
}
