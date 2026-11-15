import { AlertIcon } from "@/components/icons/alert-icon";
import { CheckIcon } from "@/components/icons/check-icon";
import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import { ButtonLink } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import { profileRoute } from "@/lib/routes";
import { counties } from "./data";
import { EdgeCaseNote } from "./edge-case-note";
import { validateFieldGeometry } from "./geometry";
import { boundarySourceLabel, fieldClassLabel, fieldName, isInDomain } from "./labels";
import type { DemoField } from "./types";

const ACRES_PER_HECTARE = 2.47105;

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-1 py-3 sm:grid-cols-[9rem_1fr] sm:gap-4">
      <dt className="text-sm font-medium text-ink-faint">{label}</dt>
      <dd className="space-y-1.5 text-[0.9375rem]">{children}</dd>
    </div>
  );
}

/**
 * Shows the result of validating the selected field's boundary (FR-01) and the way forward.
 * The validation runs on the field's real geometry; the result is never hard-coded.
 *
 * On desktop the panel sits under the sticky map: the header (status and the call to action)
 * stays visible and the details scroll inside the panel.
 */
export function FieldSummaryPanel({ field }: { field: DemoField }) {
  const report = validateFieldGeometry(field.ring, counties);
  const name = fieldName(field);
  const areaHa = report.areaHa ?? field.areaHa;

  return (
    <section
      aria-labelledby="field-summary-title"
      className="flex min-h-0 flex-col rounded-[var(--radius-card)] border border-line bg-surface shadow-card lg:max-h-[36dvh]"
    >
      <header className="flex flex-col gap-4 p-5 sm:flex-row sm:items-start sm:justify-between sm:p-6">
        <div className="flex items-start gap-3">
          <span
            aria-hidden
            className={cn(
              "mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full",
              report.valid
                ? "bg-forest-100 text-forest-700"
                : "bg-clay-100 text-clay-700",
            )}
          >
            {report.valid ? (
              <CheckIcon className="size-4" strokeWidth="2.4" />
            ) : (
              <AlertIcon className="size-4" strokeWidth="2.4" />
            )}
          </span>
          <div>
            <h2
              id="field-summary-title"
              className="font-display text-xl font-semibold sm:text-2xl"
            >
              {name} {report.valid ? "is valid and ready" : "needs fixing"}
            </h2>
            {report.valid ? (
              <p className="mt-1 text-[0.9375rem] text-ink-soft">
                A closed shape that does not cross itself, inside {report.county} County.
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

        {report.valid ? (
          <ButtonLink href={profileRoute(field.id)} className="shrink-0">
            Build field profile
          </ButtonLink>
        ) : (
          <span
            aria-disabled="true"
            className="inline-flex min-h-12 shrink-0 cursor-not-allowed items-center justify-center rounded-full bg-sunken px-6 text-base font-semibold text-ink-faint"
          >
            Build field profile
          </span>
        )}
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto border-t border-line px-5 pb-5 sm:px-6 sm:pb-6">
        <dl className="divide-y divide-line">
          <Row label="Where and size">
            {field.county} County, Iowa · {areaHa.toFixed(1)} ha (
            {Math.round(areaHa * ACRES_PER_HECTARE)} acres)
          </Row>
          <Row label="Boundary">
            <p>
              <span className="font-medium">
                {boundarySourceLabel[field.boundarySource]}.
              </span>{" "}
              <span className="text-ink-soft">
                Drawn by the AgroCycle team, not a real farm boundary.
              </span>
            </p>
            <EvidenceBadge type="assumption" />
            <details className="text-sm text-ink-faint">
              <summary className="-my-3 cursor-pointer py-3 font-medium text-forest-700">
                Where this boundary came from
              </summary>
              <p className="mt-2">{field.provenance}</p>
            </details>
          </Row>
          <Row label="Crop history type">
            <p>
              <span className="font-medium">{fieldClassLabel[field.fieldClass]}.</span>{" "}
              <span className="text-ink-soft">
                From the USDA crop map. The year-by-year history comes next.
              </span>
            </p>
            <EvidenceBadge type="classified" />
          </Row>
        </dl>

        {!isInDomain(field) ? <EdgeCaseNote className="mt-4" /> : null}
      </div>
    </section>
  );
}
