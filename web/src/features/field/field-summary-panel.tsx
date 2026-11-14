import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import { ButtonLink } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import { profileRoute } from "@/lib/routes";
import { counties } from "./data";
import { validateFieldGeometry } from "./geometry";
import { boundarySourceLabel, fieldClassLabel, fieldName, isInDomain } from "./labels";
import type { DemoField } from "./types";

const ACRES_PER_HECTARE = 2.47105;

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-1 py-3 sm:grid-cols-[11rem_1fr] sm:gap-4">
      <dt className="text-sm font-medium text-ink-faint">{label}</dt>
      <dd className="space-y-2 text-[0.9375rem]">{children}</dd>
    </div>
  );
}

/**
 * Shows the result of validating the selected field's boundary (FR-01) and the way forward.
 * The validation runs on the field's real geometry; the result is never hard-coded.
 */
export function FieldSummaryPanel({ field }: { field: DemoField }) {
  const report = validateFieldGeometry(field.ring, counties);
  const name = fieldName(field);
  const areaHa = report.areaHa ?? field.areaHa;

  return (
    <section
      aria-labelledby="field-summary-title"
      className="rounded-[var(--radius-card)] border border-line bg-surface p-6 shadow-card sm:p-8"
    >
      <div className="flex items-start gap-3">
        <span
          aria-hidden
          className={cn(
            "mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full",
            report.valid ? "bg-forest-100 text-forest-700" : "bg-clay-100 text-clay-700",
          )}
        >
          <svg
            viewBox="0 0 20 20"
            className="size-4"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d={report.valid ? "M4 10.5l4 4 8-9" : "M10 5v6M10 14.5v.5"} />
          </svg>
        </span>
        <div>
          <h2 id="field-summary-title" className="font-display text-2xl font-semibold">
            {name} {report.valid ? "is valid and ready" : "needs fixing"}
          </h2>
          {report.valid ? (
            <p className="mt-1 text-ink-soft">
              The boundary is a closed shape that does not cross itself and sits inside{" "}
              {report.county} County.
            </p>
          ) : (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-clay-700">
              {report.issues.map((issue) => (
                <li key={issue.code}>{issue.message}</li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <dl className="mt-6 divide-y divide-line border-t border-line">
        <Row label="Where">{field.county} County, Iowa</Row>
        <Row label="Size">
          {areaHa.toFixed(1)} ha ({Math.round(areaHa * ACRES_PER_HECTARE)} acres)
        </Row>
        <Row label="Boundary">
          <p className="font-medium">{boundarySourceLabel[field.boundarySource]}</p>
          <p className="text-ink-soft">
            Drawn by the AgroCycle team, not a real farm boundary.
          </p>
          <EvidenceBadge type="assumption" />
          <details className="text-sm text-ink-faint">
            <summary className="cursor-pointer font-medium text-forest-700">
              Where this boundary came from
            </summary>
            <p className="mt-2">{field.provenance}</p>
          </details>
        </Row>
        <Row label="Crop history type">
          <p className="font-medium">{fieldClassLabel[field.fieldClass]}</p>
          <p className="text-ink-soft">
            Picked from the USDA crop map. The full year-by-year history comes next.
          </p>
          <EvidenceBadge type="classified" />
        </Row>
      </dl>

      {!isInDomain(field) ? (
        <p
          role="note"
          className="mt-5 rounded-2xl bg-clay-100 px-4 py-3 text-[0.9375rem] text-clay-700"
        >
          <strong className="font-semibold">An edge case on purpose.</strong> This field
          is not a maize–soybean rotation, which is what AgroCycle is built for. Use it to
          see how the tool handles a field the evidence does not cover. It is expected to
          say “not enough evidence” rather than compare the options.
        </p>
      ) : null}

      <div className="mt-7 flex flex-col gap-3 sm:flex-row">
        {report.valid ? (
          <ButtonLink href={profileRoute(field.id)}>Build field profile</ButtonLink>
        ) : (
          <span
            aria-disabled="true"
            className="inline-flex min-h-12 cursor-not-allowed items-center justify-center rounded-full bg-sunken px-6 text-base font-semibold text-ink-faint"
          >
            Build field profile
          </span>
        )}
      </div>
    </section>
  );
}
