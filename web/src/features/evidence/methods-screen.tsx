import Link from "next/link";
import { PageHeader } from "@/components/layout/page-header";
import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import type { EvidenceTypeId } from "@/domain/evidence";
import { evidenceTypes } from "@/domain/evidence";
import { readNotice, type ApiRead } from "@/lib/api-read";
import { indicatorRoute, routes } from "@/lib/routes";
import type { Health, IndicatorSummary, Source } from "./methods-types";

const isEvidenceType = (value: string): value is EvidenceTypeId => value in evidenceTypes;

export const Evidence = ({ type }: { type: string }) =>
  isEvidenceType(type) ? <EvidenceBadge type={type} /> : <span>{type}</span>;

const label = (indicator: IndicatorSummary) =>
  indicator.label.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());

/** `/methods`: where each number comes from, how it is worked out, and how far to trust it. */
export function MethodsScreen({
  sources,
  indicators,
  health,
}: {
  sources: ApiRead<Source[]>;
  indicators: ApiRead<IndicatorSummary[]>;
  health: ApiRead<Health>;
}) {
  return (
    <>
      <PageHeader
        eyebrow="Data and methods"
        title="Where the numbers come from"
        back={{ href: routes.home, label: "home" }}
      >
        <p>
          Every value in AgroCycle has a source, a method and a limit. This page lists
          them. Each indicator opens its own page with the full method.
        </p>
      </PageHeader>

      {health.status === "ok" ? (
        <p className="mt-4 font-mono text-xs break-words text-ink-faint">
          Rules {health.data.rules_version} · data {health.data.data_version}
        </p>
      ) : null}

      <section aria-labelledby="legend-title" className="mt-10">
        <h2 id="legend-title" className="font-display text-2xl font-semibold">
          Kinds of evidence
        </h2>
        <p className="mt-2 max-w-3xl text-ink-soft">
          Not all evidence is alike. Each source and indicator carries one of these
          labels.
        </p>
        <dl className="mt-4 grid gap-3 sm:grid-cols-2">
          {Object.entries(evidenceTypes).map(([id, type]) => (
            <div key={id} className="rounded-2xl border border-line bg-surface p-4">
              <dt>
                <EvidenceBadge type={id as EvidenceTypeId} />
              </dt>
              <dd className="mt-2 text-[0.9375rem] text-ink-soft">{type.meaning}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="sources-title" className="mt-12">
        <h2 id="sources-title" className="font-display text-2xl font-semibold">
          Data sources
        </h2>
        {sources.status !== "ok" ? (
          <Notice status={sources.status} />
        ) : (
          <ul className="mt-4 space-y-4">
            {sources.data.map((source) => (
              <li
                key={source.source_id}
                className="rounded-[var(--radius-card)] border border-line bg-surface p-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <h3 className="text-lg font-semibold">{source.product}</h3>
                  <Evidence type={source.evidence_type} />
                </div>
                <p className="text-sm text-ink-soft">{source.provider}</p>
                <dl className="mt-3 grid gap-x-8 gap-y-2 text-[0.9375rem] sm:grid-cols-[10rem_1fr]">
                  <Row term="Version">{source.product_version}</Row>
                  <Row term="Resolution">
                    {source.spatial_resolution}; {source.temporal_resolution}
                  </Row>
                  <Row term="Coverage">
                    {source.geographic_coverage}. {source.historical_coverage}.
                  </Row>
                  <Row term="Retrieved">{source.retrieval_date}</Row>
                  <Row term="Licence">{source.licence}</Row>
                  <Row term="What it cannot tell you">{source.known_limitations}</Row>
                  <Row term="Link">
                    <a
                      href={source.url}
                      className="break-words text-forest-700 underline underline-offset-4"
                    >
                      {source.url}
                    </a>
                  </Row>
                </dl>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="indicators-title" className="mt-12">
        <h2 id="indicators-title" className="font-display text-2xl font-semibold">
          Indicators
        </h2>
        {indicators.status !== "ok" ? (
          <Notice status={indicators.status} />
        ) : (
          <ul className="mt-4 grid gap-3 md:grid-cols-2">
            {indicators.data.map((indicator) => (
              <li
                key={indicator.indicator_id}
                className="rounded-2xl border border-line bg-surface p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <Link
                    href={indicatorRoute(indicator.indicator_id)}
                    className="font-semibold text-forest-700 underline underline-offset-4"
                  >
                    {label(indicator)}
                  </Link>
                  <Evidence type={indicator.evidence_type} />
                </div>
                <p className="mt-1 font-mono text-xs text-ink-faint">
                  {indicator.scale} scale · {indicator.aggregation_window}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}

function Notice({ status }: { status: Exclude<ApiRead<unknown>["status"], "ok"> }) {
  return (
    <p role="status" className="mt-3 rounded-2xl bg-sunken px-4 py-3 text-ink-soft">
      {readNotice[status]}
    </p>
  );
}

export function Row({ term, children }: { term: string; children: React.ReactNode }) {
  return (
    <>
      <dt className="text-sm font-semibold">{term}</dt>
      <dd>{children}</dd>
    </>
  );
}
