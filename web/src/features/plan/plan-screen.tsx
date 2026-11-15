import type { ReactNode } from "react";
import { PageHeader } from "@/components/layout/page-header";
import { strategies } from "@/domain/strategies";
import { EngineNotice, engineLine } from "@/features/compare/components/engine-notice";
import { EvidenceLedger } from "@/features/compare/components/evidence-ledger";
import { buildEvidenceLedger } from "@/features/compare/evidence-ledger";
import {
  comparisonBlocked,
  distinctFindings,
  feasibilityCopy,
  outcomeCopy,
} from "@/features/compare/labels";
import type { Comparison } from "@/features/compare/get-comparison";
import { boundarySourceLabel, fieldClassLabel, fieldName } from "@/features/field/labels";
import { serializeAnswers } from "@/features/priorities/answers-codec";
import { optionLabel, questions, type Answers } from "@/features/priorities/questions";
import { compareRoute, prioritiesRoute } from "@/lib/routes";
import { buildAdviserQuestions } from "./expert-questions";
import { cropHistoryPeriod, profileSources } from "./brief-sources";
import { PrintButton } from "./print-button";

function Block({
  title,
  id,
  children,
}: {
  title: string;
  id: string;
  children: ReactNode;
}) {
  return (
    <section aria-labelledby={`${id}-title`} className="mt-10 break-inside-avoid-page">
      <h2
        id={`${id}-title`}
        className="border-b border-line pb-2 font-display text-xl font-medium sm:text-2xl"
      >
        {title}
      </h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

/** Step 5: a one-page brief for a conversation with an adviser. Not a plan to follow. */
export function PlanScreen({
  comparison,
  answers,
}: {
  comparison: Comparison;
  answers: Answers;
}) {
  const { field, decision, preview, provenance, profile } = comparison;
  const answerParams = serializeAnswers(answers);
  const compareParams = new URLSearchParams(answerParams);
  if (preview) compareParams.set("preview", "sample");

  const outcome = outcomeCopy[decision.outcome];
  const blocked = comparisonBlocked(decision);
  const adviserQuestions = buildAdviserQuestions(decision, answers);
  const ledger = buildEvidenceLedger(decision, profile, { preview });
  const withheld = decision.outcomes.filter((o) => o.statement === null);
  const period = cropHistoryPeriod(profile);
  const cropProvenance = profile?.cropHistory.provenance;
  const sources = profileSources(profile);
  const priorityQuestions = questions.filter((q) => q.group === "priority");
  const high = priorityQuestions.filter((q) => answers[q.id] === "high");

  return (
    <article>
      <PageHeader
        eyebrow="Brief for an adviser"
        title={<>{fieldName(field)}: rotation options</>}
        back={{ href: compareRoute(field.id, compareParams), label: "the comparison" }}
        aside={<PrintButton />}
      >
        <p>
          {field.county} County, Iowa · {boundarySourceLabel[field.boundarySource]}
        </p>
        <p>
          This is a summary to talk through with someone who knows the land. It is
          decision support. It is not a prescription, not a farm-management plan, and not
          a prediction of yield or profit.
        </p>
      </PageHeader>

      {preview ? (
        <div
          role="note"
          className="mt-8 rounded-2xl border-2 border-harvest-500 bg-harvest-100 p-5"
        >
          <p className="font-semibold text-harvest-700">
            Sample values. This is not the field’s result.
          </p>
          <p className="mt-1 text-[0.9375rem] text-ink-soft">
            This page replaces the field’s measurements (heat, rain, frost-free days and
            soil organic matter) with sample values that are known and fine, whatever the
            data says. Do not use it to decide anything.
          </p>
        </div>
      ) : null}

      <div className="mt-8 empty:hidden">
        <EngineNotice provenance={provenance} />
      </div>

      <Block id="result" title="What we found">
        <p className="font-display text-xl font-medium sm:text-2xl">{outcome.title}</p>
        <p className="mt-2 max-w-3xl text-ink-soft">{outcome.summary}</p>
        <p className="mt-3 text-sm text-ink-faint">
          Engine reason: <q>{decision.outcome_reason}</q>
        </p>
        {distinctFindings(decision).length > 0 ? (
          <ul className="mt-4 list-disc space-y-1.5 pl-5">
            {distinctFindings(decision).map((finding) => (
              <li key={finding.rule_id}>{finding.condition_text}</li>
            ))}
          </ul>
        ) : null}
      </Block>

      <Block id="field" title="The field">
        <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-[12rem_1fr]">
          <dt className="font-semibold">Field</dt>
          <dd>
            {fieldName(field)} <span className="font-mono text-sm">({field.id})</span>,{" "}
            {field.county} County, Iowa, {field.areaHa.toFixed(1)} ha
          </dd>
          <dt className="font-semibold">Boundary</dt>
          <dd>
            <strong>{boundarySourceLabel[field.boundarySource]}.</strong>{" "}
            {field.boundarySource === "demo"
              ? "This is a demonstration field made by the AgroCycle team. It is not a real farm boundary, and nothing here is about a real farm."
              : "The boundary was drawn or supplied by the person who made this brief."}{" "}
            {field.provenance}
          </dd>
          <dt className="font-semibold">Type of field</dt>
          <dd>{fieldClassLabel[field.fieldClass]}</dd>
          <dt className="font-semibold">Crop history</dt>
          <dd>
            {decision.crop_history_summary}
            <span className="mt-1 block text-sm text-ink-soft">
              {period && cropProvenance
                ? `Period: ${period}. Source: ${cropProvenance.source}, a satellite-based classification and not a farm record. ${cropProvenance.precision}`
                : "Period and source: not available here, because the field profile could not be loaded."}
            </span>
          </dd>
        </dl>
      </Block>

      <Block id="options" title="The three options">
        <ul className="grid gap-4 md:grid-cols-3">
          {decision.strategies.map((assessment) => {
            const strategy = strategies.find((s) => s.id === assessment.strategy_id)!;
            const label =
              strategy.id === "A"
                ? "Your starting point"
                : blocked
                  ? "Not offered for this field"
                  : feasibilityCopy[assessment.feasibility].label;
            return (
              <li key={strategy.id} className="rounded-2xl border border-line p-4">
                <p className="font-semibold">
                  Option {strategy.id}: {strategy.name}
                </p>
                <p className="text-sm text-ink-soft">{assessment.rotation}</p>
                <p className="mt-1 text-sm">{strategy.summary}</p>
                <p className="mt-2 text-[0.9375rem] font-medium">{label}</p>
                {!blocked && assessment.findings.length > 0 ? (
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                    {assessment.findings.map((finding) => (
                      <li key={finding.rule_id}>{finding.condition_text}</li>
                    ))}
                  </ul>
                ) : null}
                <p className="mt-3 text-sm font-semibold">What it needs</p>
                <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-ink-soft">
                  {assessment.operational_requirements.map((requirement) => (
                    <li key={requirement}>{requirement}</li>
                  ))}
                </ul>
              </li>
            );
          })}
        </ul>
        <p className="mt-3 text-sm text-ink-faint">
          Listed by rotation length. Nothing here ranks them.
        </p>
      </Block>

      <Block id="evidence" title="Evidence used in the comparison">
        <EvidenceLedger ledger={ledger} compact />
      </Block>

      <Block id="answers" title="Your priorities and constraints">
        <p className="mb-3 text-[0.9375rem] text-ink-soft">
          {high.length > 0
            ? `Priorities marked high: ${high.map((q) => q.label.toLowerCase()).join("; ")}.`
            : "No priority was marked high."}{" "}
          Priorities change what is pointed out, not the result. Only the four constraints
          marked below are read by the rules; the others are for this conversation.
        </p>
        <dl className="divide-y divide-line rounded-2xl border border-line">
          {questions.map((question) => {
            const label = optionLabel(question, answers[question.id]);
            return (
              <div
                key={question.id}
                className="grid gap-1 px-4 py-2.5 sm:grid-cols-[1fr_12rem] sm:gap-4"
              >
                <dt className="text-[0.9375rem]">
                  {question.label}
                  {"engineKey" in question && question.engineKey ? (
                    <span className="ml-2 text-xs font-semibold tracking-wide text-ink-faint uppercase">
                      Read by the rules
                    </span>
                  ) : null}
                </dt>
                <dd className={label ? "font-semibold" : "text-ink-faint"}>
                  {label ?? "Not provided"}
                </dd>
              </div>
            );
          })}
        </dl>
        <p className="mt-3 text-sm text-ink-faint print:hidden">
          <a
            className="-my-3 inline-block py-3 font-semibold text-forest-700 underline underline-offset-4"
            href={prioritiesRoute(field.id, answerParams)}
          >
            Change my answers
          </a>
        </p>
      </Block>

      <Block id="ask" title="Questions for local expert review">
        <ol className="list-decimal space-y-2.5 pl-6">
          {adviserQuestions.map((question) => (
            <li key={question.id} className="pl-1">
              {question.text}
            </li>
          ))}
        </ol>
      </Block>

      <Block id="withheld" title="Not shown, and why">
        {withheld.length > 0 ? (
          <ul className="space-y-3">
            {withheld.map((outcome) => {
              const reasons = outcome.findings.filter((f) => f.effect !== "in_domain");
              return (
                <li key={outcome.outcome_id}>
                  <p className="font-medium">{outcome.label}</p>
                  <p className="text-sm text-ink-soft">
                    {outcome.claimable
                      ? "Held back for this field. Missing information is not treated as good or bad news."
                      : "Not assessed. We have no data that measures this on a field, so we say nothing about it."}
                  </p>
                  {reasons.length > 0 ? (
                    <ul className="mt-1 list-disc space-y-0.5 pl-5 text-sm">
                      {reasons.map((reason) => (
                        <li key={reason.rule_id}>{reason.condition_text}</li>
                      ))}
                    </ul>
                  ) : null}
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="text-[0.9375rem] text-ink-soft">
            Every outcome the engine knows about is shown for this field, each with its
            caution.
          </p>
        )}
      </Block>

      <Block id="limits" title="Limits, versions and sources">
        <ul className="list-disc space-y-1.5 pl-5 text-[0.9375rem] text-ink-soft">
          {decision.limitations.map((limitation) => (
            <li key={limitation}>{limitation}</li>
          ))}
        </ul>
        <dl className="mt-5 grid gap-x-8 gap-y-2 text-sm sm:grid-cols-[12rem_1fr]">
          <dt className="font-semibold">Engine</dt>
          <dd>{engineLine(provenance)}</dd>
          <dt className="font-semibold">Rules version</dt>
          <dd className="font-mono">{decision.rules_version}</dd>
          <dt className="font-semibold">Data version</dt>
          <dd className="font-mono">
            {provenance.dataVersion ??
              "Not recorded (the service did not run this comparison)"}
          </dd>
          {sources.map((source) => (
            <div key={`${source.source}|${source.detail}`} className="contents">
              <dt className="font-semibold">{source.use}</dt>
              <dd>
                {source.source}
                <span className="block text-ink-soft">{source.detail}</span>
              </dd>
            </div>
          ))}
        </dl>
        <p className="mt-4 text-sm text-ink-faint">
          This brief is not a prescription or a farm-management plan. AgroCycle, built for
          the NASA Space Apps Challenge 2026. An independent project, not an official NASA
          product.
        </p>
      </Block>
    </article>
  );
}
