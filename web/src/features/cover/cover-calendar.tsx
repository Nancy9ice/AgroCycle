import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import type { EvidenceTypeId } from "@/domain/evidence";
import { evidenceTypes } from "@/domain/evidence";
import { cn } from "@/lib/cn";
import { readApi, readNotice } from "@/lib/api-read";
import { cellLabel, monthNames, stateWord, yearSummary } from "./cover-text";
import type { CoverCalendar as Calendar, CoverState } from "./types";

const isEvidenceType = (value: string): value is EvidenceTypeId => value in evidenceTypes;

const cellStyle: Record<CoverState, string> = {
  bare: "border-clay-700 bg-clay-100 text-clay-700",
  likely_bare: "border-dashed border-clay-700/60 bg-clay-100/50 text-clay-700",
  green: "border-forest-300 bg-forest-100 text-forest-800",
  unknown: "border-dashed border-line-strong bg-sunken text-ink-faint",
};

/**
 * What satellite images say about cover on this field, month by month (F3, observed). It does not say which
 * crop grew, and it shows nothing for the three-year or four-year rotations: no sourced timing exists for them.
 */
export async function CoverCalendar({ fieldId }: { fieldId: string }) {
  const result = await readApi<Calendar>(
    `/fields/${encodeURIComponent(fieldId)}/cover-calendar`,
  );
  if (result.status === "not_found") {
    return (
      <p role="status" className="rounded-2xl bg-sunken px-4 py-3 text-ink-soft">
        No satellite images have been loaded for this field, so there is no cover calendar
        to show.
      </p>
    );
  }
  if (result.status !== "ok") {
    return (
      <p role="status" className="rounded-2xl bg-sunken px-4 py-3 text-ink-soft">
        {readNotice[result.status]}
      </p>
    );
  }
  const calendar = result.data;
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3 text-sm text-ink-soft">
        {isEvidenceType(calendar.evidence_type) ? (
          <EvidenceBadge type={calendar.evidence_type} />
        ) : null}
        <span>{calendar.source}</span>
      </div>

      <div className="overflow-x-auto rounded-[var(--radius-card)] border border-line bg-surface">
        <table className="w-full min-w-[46rem] border-separate border-spacing-1 p-2 text-center text-xs">
          <caption className="sr-only">
            Cover on this field by month, from satellite images, for each year with images
          </caption>
          <thead>
            <tr>
              <th scope="col" className="w-14 text-left font-mono text-ink-faint">
                Year
              </th>
              {monthNames.map((name) => (
                <th
                  key={name}
                  scope="col"
                  className="font-mono font-medium text-ink-faint"
                >
                  {name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {calendar.years.map((year) => (
              <tr key={year.year}>
                <th scope="row" className="text-left font-mono font-semibold">
                  {year.year}
                </th>
                {year.months.map((month) => (
                  <td
                    key={month.month}
                    title={cellLabel(year.year, month)}
                    aria-label={cellLabel(year.year, month)}
                    className={cn(
                      "rounded-md border px-1 py-2 font-medium",
                      cellStyle[month.state],
                    )}
                  >
                    {stateWord[month.state]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ul className="space-y-1 text-[0.9375rem]">
        {calendar.years.map((year) => (
          <li key={year.year}>{yearSummary(year)}</li>
        ))}
      </ul>

      <dl className="grid gap-2 text-sm text-ink-soft sm:grid-cols-2">
        {(Object.keys(stateWord) as CoverState[]).map((state) => (
          <div key={state} className="flex gap-2">
            <dt
              className={cn(
                "h-fit shrink-0 rounded-md border px-2 py-0.5 text-xs font-medium",
                cellStyle[state],
              )}
            >
              {stateWord[state]}
            </dt>
            <dd>{calendar.legend[state].replace(/^[^:]+: /, "")}</dd>
          </div>
        ))}
      </dl>

      <ul className="max-w-3xl list-disc space-y-1 pl-5 text-sm text-ink-soft">
        {calendar.caveats.map((caveat) => (
          <li key={caveat}>{caveat}</li>
        ))}
      </ul>
    </div>
  );
}
