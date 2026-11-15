import Link from "next/link";
import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import { PageHeader } from "@/components/layout/page-header";
import { cn } from "@/lib/cn";
import { readNotice, type ApiRead } from "@/lib/api-read";
import { compareRoute, prioritiesRoute, switchRoute } from "@/lib/routes";
import {
  basisLabel,
  readinessNote,
  readinessWord,
  stepHeading,
  strategyTabs,
  timingLine,
} from "./text";
import type { Transition, TransitionStep } from "./types";

/** Step 5: one way to switch to B or C, year by year. A starting point for an adviser, never a final plan. */
export function TransitionScreen({
  fieldId,
  strategy,
  analysisId,
  result,
}: {
  fieldId: string;
  strategy: string;
  analysisId?: string;
  result: ApiRead<Transition>;
}) {
  return (
    <>
      <PageHeader
        eyebrow="Plan the switch"
        title="One way to switch, year by year"
        back={{ href: compareRoute(fieldId), label: "the comparison" }}
      >
        <p>
          A starting point for your adviser, not a final plan. We only show what the
          Marsden Farm experiment establishes. Where it gives no timing, we say so instead
          of guessing.
        </p>
      </PageHeader>

      <nav aria-label="Which rotation" className="mt-6 flex flex-wrap gap-2">
        {strategyTabs.map((tab) => (
          <Link
            key={tab.id}
            href={switchRoute(fieldId, tab.id, analysisId)}
            aria-current={tab.id === strategy ? "page" : undefined}
            className={cn(
              "inline-flex min-h-11 items-center rounded-full border px-5 text-[0.9375rem] font-semibold",
              tab.id === strategy
                ? "border-forest-700 bg-forest-700 text-white"
                : "border-line-strong bg-surface text-ink hover:border-forest-600",
            )}
          >
            {tab.label}
          </Link>
        ))}
      </nav>

      {result.status !== "ok" ? (
        <p role="status" className="mt-8 rounded-2xl bg-sunken px-4 py-3 text-ink-soft">
          {readNotice[result.status]}
        </p>
      ) : (
        <Plan fieldId={fieldId} transition={result.data} />
      )}
    </>
  );
}

function Plan({ fieldId, transition }: { fieldId: string; transition: Transition }) {
  return (
    <>
      <p className="mt-6 text-lg font-medium">{transition.rotation}</p>

      {transition.readiness ? (
        <section
          aria-labelledby="ready-title"
          className="mt-6 rounded-[var(--radius-card)] border border-line bg-surface p-5 sm:p-6"
        >
          <h2 id="ready-title" className="font-display text-xl font-semibold">
            Are you ready?
          </h2>
          <p className="mt-1 text-sm text-ink-soft">
            From the answers you gave when you compared. A skipped answer counts as not
            answered, never as no.
          </p>
          <ul className="mt-4 divide-y divide-line">
            {transition.readiness.map((item) => (
              <li
                key={item.constraint}
                className="grid gap-1 py-3 sm:grid-cols-[1fr_8rem] sm:gap-4"
              >
                <div>
                  <p className="font-semibold">{item.label}</p>
                  <p className="text-sm text-ink-soft">{readinessNote(item)}</p>
                </div>
                <p
                  className={cn(
                    "h-fit w-fit rounded-full border px-3 py-1 text-sm font-semibold",
                    item.status === "yes" &&
                      "border-forest-300 bg-forest-100 text-forest-800",
                    item.status === "no" && "border-clay-700 bg-clay-100 text-clay-700",
                    item.status === "not_answered" &&
                      "border-dashed border-line-strong bg-sunken text-ink-soft",
                  )}
                >
                  {readinessWord[item.status]}
                </p>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-sm">
            <Link
              href={prioritiesRoute(fieldId)}
              className="font-semibold text-forest-700 underline underline-offset-4"
            >
              Change my answers
            </Link>
          </p>
        </section>
      ) : null}

      <ol className="mt-8 space-y-4">
        {transition.steps.map((step) => (
          <li key={step.year}>
            <StepCard fieldId={fieldId} step={step} />
          </li>
        ))}
      </ol>

      <ul className="mt-8 max-w-3xl list-disc space-y-1 pl-5 text-sm text-ink-soft">
        {transition.caveats.map((caveat) => (
          <li key={caveat}>{caveat}</li>
        ))}
      </ul>
      <p className="mt-3 font-mono text-xs break-words text-ink-faint">
        Rules {transition.rules_version} · data {transition.data_version}
      </p>
    </>
  );
}

function StepCard({ fieldId, step }: { fieldId: string; step: TransitionStep }) {
  return (
    <article className="rounded-[var(--radius-card)] border border-line bg-surface p-5 sm:p-6">
      <header className="flex flex-wrap items-start justify-between gap-2">
        <h2 className="font-display text-lg font-semibold sm:text-xl">
          {stepHeading(step)}
        </h2>
        {step.evidence_basis === "experimental" ? (
          <EvidenceBadge type="experimental" />
        ) : (
          <span className="rounded-full border border-dashed border-line-strong px-2.5 py-1 font-mono text-xs text-ink-soft">
            {step.evidence_basis === "team_proposed"
              ? "Team’s own reading"
              : "Assumption"}
          </span>
        )}
      </header>
      <p className="mt-2 text-[0.9375rem]">{step.action}</p>

      <p
        className={cn(
          "mt-3 rounded-xl px-3 py-2 text-sm",
          step.timing_established
            ? "bg-forest-50 text-forest-800"
            : "bg-sunken text-ink-soft",
        )}
      >
        {timingLine(step)}
      </p>

      <h3 className="mt-4 text-sm font-semibold">You will need</h3>
      <ul className="mt-1 list-disc space-y-0.5 pl-5 text-[0.9375rem]">
        {step.needs.map((need) => (
          <li key={need}>{need}</li>
        ))}
      </ul>

      {step.shows_past_weather ? (
        <p className="mt-4 text-sm">
          <Link
            href={`${compareRoute(fieldId)}#seasons-title`}
            className="font-semibold text-forest-700 underline underline-offset-4"
          >
            See how past seasons looked in your field’s weather
          </Link>{" "}
          <span className="text-ink-soft">
            (counts over whole seasons, not tied to any stage)
          </span>
        </p>
      ) : null}

      <p className="mt-3 text-xs text-ink-faint">
        {basisLabel(step.evidence_basis)}. {step.source}
      </p>
    </article>
  );
}
