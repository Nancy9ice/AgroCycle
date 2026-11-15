import { AlertIcon } from "@/components/icons/alert-icon";
import { ArrowRightIcon } from "@/components/icons/arrow-right-icon";
import { CheckIcon } from "@/components/icons/check-icon";
import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import { ButtonLink } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import { profileRoute } from "@/lib/routes";
import { EdgeCaseNote } from "./edge-case-note";
import { validateFieldGeometry } from "./geometry";
import { boundarySourceLabel, fieldClassLabel, fieldName, isInDomain } from "./labels";
import type { County, DemoField } from "./types";

const ACRES_PER_HECTARE = 2.47105;

/**
 * The selected field and the one thing to do next. The boundary is validated here on the field's real
 * geometry (FR-01); the result is never hard-coded. Detail is one tap away, not in the way.
 */
export function FieldSummaryPanel({
  field,
  counties,
}: {
  field: DemoField;
  counties: readonly County[];
}) {
  const report = validateFieldGeometry(field.ring, counties);
  const name = fieldName(field);
  const areaHa = report.areaHa ?? field.areaHa;

  return (
    <section
      aria-labelledby="field-summary-title"
      className="rounded-[var(--radius-card)] border border-line bg-surface p-5 shadow-card"
    >
      <div className="flex items-start gap-3">
        <span
          aria-hidden
          className={cn(
            "mt-1 flex size-8 shrink-0 items-center justify-center rounded-full",
            report.valid ? "bg-forest-100 text-forest-700" : "bg-clay-100 text-clay-700",
          )}
        >
          {report.valid ? (
            <CheckIcon className="size-4" strokeWidth="2.4" />
          ) : (
            <AlertIcon className="size-4" strokeWidth="2.4" />
          )}
        </span>
        <div className="min-w-0">
          <p className="font-mono text-[0.6875rem] tracking-[0.12em] text-ink-faint uppercase">
            Selected field
          </p>
          <h2
            id="field-summary-title"
            className="font-display text-xl leading-tight font-medium sm:text-2xl"
          >
            {name}
          </h2>
          <p className="mt-1 text-[0.8125rem] text-ink-soft sm:text-sm">
            {field.county} County, Iowa · {areaHa.toFixed(1)} ha (
            {Math.round(areaHa * ACRES_PER_HECTARE)} acres)
          </p>
          <p
            className={cn(
              "mt-1 text-[0.8125rem] sm:text-sm",
              report.valid ? "text-forest-700" : "text-clay-700",
            )}
          >
            {report.valid ? "Boundary is valid and ready" : "Boundary needs fixing"}
          </p>
        </div>
      </div>

      {!report.valid ? (
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-clay-700">
          {report.issues.map((issue) => (
            <li key={issue.code}>{issue.message}</li>
          ))}
        </ul>
      ) : null}

      {report.valid ? (
        <ButtonLink
          href={profileRoute(field.id)}
          className="mt-4 min-h-11 w-full text-sm font-medium"
        >
          Build field profile <ArrowRightIcon className="size-4" />
        </ButtonLink>
      ) : (
        <span
          aria-disabled="true"
          className="mt-4 inline-flex min-h-11 w-full cursor-not-allowed items-center justify-center rounded-full bg-sunken px-6 text-sm font-medium text-ink-faint"
        >
          Build field profile
        </span>
      )}

      <details className="group mt-3 text-sm">
        <summary className="-my-1 flex min-h-11 cursor-pointer list-none items-center justify-between text-[0.8125rem] font-medium text-forest-700 [&::-webkit-details-marker]:hidden">
          About this field
          <span aria-hidden className="text-lg leading-none group-open:hidden">
            +
          </span>
          <span aria-hidden className="hidden text-lg leading-none group-open:inline">
            −
          </span>
        </summary>
        <dl className="mt-1 max-h-64 space-y-4 overflow-y-auto border-t border-line pt-4 pr-1">
          <div className="space-y-1.5">
            <dt className="font-medium text-ink-faint">Boundary</dt>
            <dd className="space-y-1.5">
              <p>
                <span className="font-medium">
                  {boundarySourceLabel[field.boundarySource]}.
                </span>{" "}
                <span className="text-ink-soft">
                  Drawn by the AgroCycle team, not a real farm boundary.
                </span>
              </p>
              <EvidenceBadge type="assumption" />
              <p className="text-ink-faint">{field.provenance}</p>
            </dd>
          </div>
          <div className="space-y-1.5">
            <dt className="font-medium text-ink-faint">Crop history type</dt>
            <dd className="space-y-1.5">
              <p>
                <span className="font-medium">{fieldClassLabel[field.fieldClass]}.</span>{" "}
                <span className="text-ink-soft">
                  From the USDA crop map. The year-by-year history comes next.
                </span>
              </p>
              <EvidenceBadge type="classified" />
            </dd>
          </div>
        </dl>
        {!isInDomain(field) ? <EdgeCaseNote className="mt-4" /> : null}
      </details>
    </section>
  );
}
