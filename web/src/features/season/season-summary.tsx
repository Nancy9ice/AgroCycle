import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import type { EvidenceTypeId } from "@/domain/evidence";
import { evidenceTypes } from "@/domain/evidence";
import { cn } from "@/lib/cn";
import { readApi, readNotice } from "@/lib/api-read";
import { barHeights, formatSeasonValue, headline } from "./season-text";
import type { SeasonIndicator, SeasonSummary as Summary } from "./types";

const isEvidenceType = (value: string): value is EvidenceTypeId => value in evidenceTypes;

/**
 * How hot, dry and wet each past season was in this field's weather cell (F2). Counts over a whole season, read
 * from the API. It never says when in the season anything happened, and says so.
 */
export async function SeasonSummary({ fieldId }: { fieldId: string }) {
  const result = await readApi<Summary>(
    `/fields/${encodeURIComponent(fieldId)}/season-summary`,
  );
  if (result.status !== "ok") {
    return (
      <p role="status" className="rounded-2xl bg-sunken px-4 py-3 text-ink-soft">
        {readNotice[result.status]}
      </p>
    );
  }
  const { indicators, caveats, period } = result.data;
  if (indicators.length === 0) {
    return (
      <p role="status" className="rounded-2xl bg-sunken px-4 py-3 text-ink-soft">
        No weather has been loaded for this field yet, so there is no season history to
        show.
      </p>
    );
  }
  return (
    <div className="space-y-6">
      <p className="max-w-3xl text-sm text-ink-soft">
        Seasons {period}, one bar per season.
      </p>
      <ul className="grid gap-4 md:grid-cols-2">
        {indicators.map((indicator) => (
          <li key={indicator.indicator_id}>
            <IndicatorCard indicator={indicator} />
          </li>
        ))}
      </ul>
      <ul className="max-w-3xl list-disc space-y-1 pl-5 text-sm text-ink-soft">
        {caveats.map((caveat) => (
          <li key={caveat}>{caveat}</li>
        ))}
      </ul>
    </div>
  );
}

function IndicatorCard({ indicator }: { indicator: SeasonIndicator }) {
  const heights = barHeights(indicator.seasons);
  const text = headline(indicator);
  const partial = indicator.seasons_used < indicator.seasons_total;
  return (
    <article className="h-full rounded-[var(--radius-card)] border border-line bg-surface p-5">
      <header className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="font-semibold">{indicator.label}</h3>
        {isEvidenceType(indicator.evidence_type) ? (
          <EvidenceBadge type={indicator.evidence_type} />
        ) : null}
      </header>
      <p className="mt-1 text-[0.9375rem]">{text}</p>

      <div
        role="img"
        aria-label={`${indicator.label}, one bar per season. ${text}`}
        className="mt-4 flex h-24 items-end gap-1"
      >
        {indicator.seasons.map((season, index) => {
          const height = heights[index];
          const isHigh = indicator.highest?.year === season.year;
          const isLow = indicator.lowest?.year === season.year;
          return (
            <div
              key={season.year}
              className="flex h-full flex-1 flex-col justify-end"
              title={
                season.value === null
                  ? `${season.year}: no figure`
                  : `${season.year}: ${formatSeasonValue(season.value)} ${indicator.unit}`
              }
            >
              {height === null ? (
                <div className="h-2 rounded-sm border border-dashed border-line-strong" />
              ) : (
                <div
                  className={cn(
                    "rounded-sm",
                    isHigh ? "bg-clay-700" : isLow ? "bg-forest-800" : "bg-forest-300",
                  )}
                  style={{ height: `${height}%` }}
                />
              )}
            </div>
          );
        })}
      </div>
      <div
        aria-hidden
        className="mt-1 flex justify-between font-mono text-xs text-ink-faint"
      >
        <span>{indicator.seasons[0]?.year}</span>
        <span>{indicator.seasons.at(-1)?.year}</span>
      </div>
      {partial ? (
        <p className="mt-2 text-sm text-ink-soft">
          {indicator.seasons_used} of {indicator.seasons_total} seasons have a figure. A
          season with no figure is shown as an empty dashed bar, not as zero.
        </p>
      ) : null}

      <details className="mt-3 text-sm">
        <summary className="cursor-pointer font-semibold text-forest-700">
          Figures and limits
        </summary>
        <table className="mt-2 w-full text-left">
          <caption className="sr-only">{indicator.label} by season</caption>
          <thead className="text-xs text-ink-faint uppercase">
            <tr>
              <th scope="col" className="py-1">
                Season
              </th>
              <th scope="col" className="py-1">
                {indicator.unit}
              </th>
            </tr>
          </thead>
          <tbody>
            {indicator.seasons.map((season) => (
              <tr key={season.year} className="border-t border-line">
                <th scope="row" className="py-1 font-mono font-normal">
                  {season.year}
                </th>
                <td className="py-1 font-mono">
                  {season.value === null
                    ? `no figure${season.unknown_reason ? ` (${season.unknown_reason})` : ""}`
                    : formatSeasonValue(season.value)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-2 text-ink-soft">{indicator.limitation}</p>
        <p className="mt-1 font-mono text-xs break-words text-ink-faint">
          {indicator.formula}
        </p>
      </details>
    </article>
  );
}
