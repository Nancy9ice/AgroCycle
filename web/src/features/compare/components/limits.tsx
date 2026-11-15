import Link from "next/link";
import { routes } from "@/lib/routes";
import { ruleTable } from "../rules";

/** Standing limitations, and the claims about crops we could not source (PRD 7.5, FR-08). */
export function Limits({ limitations }: { limitations: readonly string[] }) {
  const unsourced = ruleTable.cropClaims.filter(
    (claim) => claim.status === "research_needed",
  );
  return (
    <div className="grid gap-5 md:grid-cols-2">
      <section
        aria-labelledby="limits-title"
        className="rounded-[var(--radius-card)] border border-line bg-surface p-6"
      >
        <h3 id="limits-title" className="font-display text-xl font-semibold">
          What this does not tell you
        </h3>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-[0.9375rem] text-ink-soft">
          {limitations.map((limitation) => (
            <li key={limitation}>{limitation}</li>
          ))}
        </ul>
        <p className="mt-4 text-sm">
          <Link
            href={routes.validation}
            className="-my-3 inline-block py-3 font-semibold text-forest-700 underline underline-offset-4"
          >
            How we checked this
          </Link>
        </p>
      </section>

      <section
        aria-labelledby="unsourced-title"
        className="rounded-[var(--radius-card)] border border-line bg-surface p-6"
      >
        <h3 id="unsourced-title" className="font-display text-xl font-semibold">
          Ideas we could not source
        </h3>
        <p className="mt-1 text-sm text-ink-soft">
          Often said about these crops, but we have not found a citable source yet, so we
          do not present them as findings.
        </p>
        <ul className="mt-3 list-disc space-y-1.5 pl-5 text-[0.9375rem]">
          {unsourced.map((claim) => (
            <li key={claim.claim_id}>{claim.claim}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
