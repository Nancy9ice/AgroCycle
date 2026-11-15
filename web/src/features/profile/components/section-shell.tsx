import type { ReactNode } from "react";
import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import { evidenceTypes } from "@/domain/evidence";
import { cn } from "@/lib/cn";
import type { Provenance, SectionStatus } from "../types";
import { ProvenanceButton } from "./provenance-button";

interface SectionShellProps {
  id: string;
  title: string;
  intro?: ReactNode;
  status: SectionStatus;
  /** Section-level provenance. Omit when each card carries its own. */
  provenance?: Provenance | null;
  /** Shown on sample sections to say what is missing. */
  sampleNote?: string;
  children: ReactNode;
}

/** Common frame for a profile section: heading, status label, content, evidence footer. */
export function SectionShell({
  id,
  title,
  intro,
  status,
  provenance,
  sampleNote,
  children,
}: SectionShellProps) {
  const isSample = status === "sample";
  return (
    <section
      aria-labelledby={`${id}-title`}
      className="rounded-[var(--radius-card)] border border-line bg-surface/60 p-6 sm:p-8"
    >
      <header className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <h2
          id={`${id}-title`}
          className="font-display text-2xl font-semibold sm:text-3xl"
        >
          {title}
        </h2>
        {isSample ? (
          <span className="rounded-full bg-harvest-100 px-3 py-1 font-mono text-xs font-medium text-harvest-700">
            Sample values
          </span>
        ) : null}
      </header>
      {intro ? <p className="mt-3 max-w-3xl text-ink-soft">{intro}</p> : null}
      {isSample && sampleNote ? (
        <p
          role="note"
          className="mt-4 max-w-3xl rounded-2xl bg-harvest-100 px-4 py-3 text-[0.9375rem] text-harvest-700"
        >
          <strong className="font-semibold">Placeholder numbers.</strong> {sampleNote}
        </p>
      ) : null}

      <div className="mt-6">{children}</div>

      {provenance ? (
        <footer
          className={cn(
            "mt-6 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-line pt-4",
          )}
        >
          <EvidenceBadge type={provenance.technical.evidenceType} />
          <span className="text-sm text-ink-faint">
            {evidenceTypes[provenance.technical.evidenceType].plain}
          </span>
          <ProvenanceButton
            provenance={provenance}
            isSample={isSample}
            className="sm:ml-auto"
          />
        </footer>
      ) : null}
    </section>
  );
}
