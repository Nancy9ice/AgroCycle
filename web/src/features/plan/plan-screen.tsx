import type { ReactNode } from "react";
import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import { ButtonLink } from "@/components/ui/button";
import { strategies } from "@/domain/strategies";
import {
  comparisonBlocked,
  distinctFindings,
  feasibilityCopy,
  outcomeCopy,
} from "@/features/compare/labels";
import type { Comparison } from "@/features/compare/get-comparison";
import { ruleTable } from "@/features/compare/rules";
import { boundarySourceLabel, fieldName } from "@/features/field/labels";
import { serializeAnswers } from "@/features/priorities/answers-codec";
import { optionLabel, questions, type Answers } from "@/features/priorities/questions";
import { compareRoute, prioritiesRoute } from "@/lib/routes";
import { buildAdviserQuestions } from "./expert-questions";
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
        className="border-b border-line pb-2 font-display text-2xl font-semibold"
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
  const { field, decision, preview } = comparison;
  const answerParams = serializeAnswers(answers);
  const compareParams = new URLSearchParams(answerParams);
  if (preview) compareParams.set("preview", "sample");

  const outcome = outcomeCopy[decision.outcome];
  const blocked = comparisonBlocked(decision);
  const adviserQuestions = buildAdviserQuestions(decision, answers);
  const claimable = decision.outcomes.filter((o) => o.claimable && o.evidence_type);

  return (
    <article>
      <header>
        <p className="font-mono text-xs font-medium tracking-[0.14em] text-forest-600 uppercase">
          Brief for an adviser
        </p>
        <h1 className="mt-2 font-display text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
          {fieldName(field)}: rotation options
        </h1>
        <p className="mt-3 text-lg text-ink-soft">
          {field.county} County, Iowa · {boundarySourceLabel[field.boundarySource]}
        </p>
        <p className="mt-3 max-w-3xl text-ink-soft">
          This is a summary to talk through with someone who knows the land. It is
          decision support, not a prescription, and not a prediction of yield or profit.
        </p>
        <div className="mt-5 flex flex-wrap gap-3 print:hidden">
          <PrintButton />
          <ButtonLink href={compareRoute(field.id, compareParams)} variant="secondary">
            Back to the comparison
          </ButtonLink>
        </div>
      </header>

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

      <Block id="result" title="What we found">
        <p className="font-display text-2xl font-semibold">{outcome.title}</p>
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
        <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-[10rem_1fr]">
          <dt className="font-semibold">Crop history</dt>
          <dd>{decision.crop_history_summary}</dd>
          <dt className="font-semibold">Boundary</dt>
          <dd>
            {boundarySourceLabel[field.boundarySource]}: {field.provenance}
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
                <p className="mt-2 text-[0.9375rem] font-medium">{label}</p>
                {!blocked && assessment.findings.length > 0 ? (
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                    {assessment.findings.map((finding) => (
                      <li key={finding.rule_id}>{finding.condition_text}</li>
                    ))}
                  </ul>
                ) : null}
              </li>
            );
          })}
        </ul>
        <p className="mt-3 text-sm text-ink-faint">
          Listed by rotation length. Nothing here ranks them.
        </p>
      </Block>

      <Block id="answers" title="What you told us">
        <dl className="divide-y divide-line rounded-2xl border border-line">
          {questions.map((question) => {
            const label = optionLabel(question, answers[question.id]);
            return (
              <div
                key={question.id}
                className="grid gap-1 px-4 py-2.5 sm:grid-cols-[1fr_12rem] sm:gap-4"
              >
                <dt className="text-[0.9375rem]">{question.label}</dt>
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

      <Block id="ask" title="Questions to ask">
        <ol className="list-decimal space-y-2.5 pl-6">
          {adviserQuestions.map((question) => (
            <li key={question.id} className="pl-1">
              {question.text}
            </li>
          ))}
        </ol>
      </Block>

      <Block id="sources" title="Where the evidence comes from">
        <ul className="space-y-3">
          {claimable.map((outcome) => (
            <li
              key={outcome.outcome_id}
              className="flex flex-wrap items-center gap-x-3 gap-y-1"
            >
              <span className="font-medium">{outcome.label}</span>
              {outcome.evidence_type ? (
                <EvidenceBadge type={outcome.evidence_type} />
              ) : null}
              <span className="text-sm text-ink-soft">{outcome.source}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-sm text-ink-faint">
          Not assessed, with no data behind them:{" "}
          {decision.outcomes
            .filter((o) => !o.claimable)
            .map((o) => o.label.toLowerCase())
            .join("; ")}
          .
        </p>
      </Block>

      <Block id="limits" title="Limits">
        <ul className="list-disc space-y-1.5 pl-5 text-[0.9375rem] text-ink-soft">
          {decision.limitations.map((limitation) => (
            <li key={limitation}>{limitation}</li>
          ))}
        </ul>
        <p className="mt-3 text-sm text-ink-faint">
          Rules version <span className="font-mono">{ruleTable.rulesVersion}</span>.
          AgroCycle, built for the NASA Space Apps Challenge 2026. An independent project,
          not an official NASA product.
        </p>
      </Block>
    </article>
  );
}
