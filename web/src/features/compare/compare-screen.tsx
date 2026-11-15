import type { ReactNode } from "react";
import Link from "next/link";
import { ButtonLink } from "@/components/ui/button";
import { apiBaseUrl } from "@/lib/api";
import { boundarySourceLabel, fieldClassLabel, fieldName } from "@/features/field/labels";
import { serializeAnswers } from "@/features/priorities/answers-codec";
import { countAnswered } from "@/features/priorities/answers-codec";
import { TOTAL_QUESTIONS, type Answers } from "@/features/priorities/questions";
import {
  compareRoute,
  fieldRoute,
  planRoute,
  prioritiesRoute,
  profileRoute,
} from "@/lib/routes";
import { AskPanel } from "@/features/ask/ask-panel";
import { askAnalysis } from "@/features/ask/actions";
import { EngineNotice, engineLine } from "./components/engine-notice";
import { EvidenceLedger } from "./components/evidence-ledger";
import { OpenQuestions } from "./components/open-questions";
import { Limits } from "./components/limits";
import { OutcomeBanner } from "./components/outcome-banner";
import { OutcomeCards } from "./components/outcome-cards";
import { PreviewNotice } from "./components/preview-notice";
import { PrioritiesPanel } from "./components/priorities-panel";
import { StrategyCards } from "./components/strategy-cards";
import { buildEvidenceLedger } from "./evidence-ledger";
import type { Comparison } from "./get-comparison";
import { hasMissingIndicators } from "./labels";
import { highlightedOutcomeIds, readPriorities } from "./priority-links";

function Block({
  id,
  title,
  intro,
  children,
}: {
  id: string;
  title: string;
  intro?: string;
  children: ReactNode;
}) {
  return (
    <section aria-labelledby={`${id}-title`} className="mt-14">
      <h2
        id={`${id}-title`}
        className="font-display text-2xl font-semibold tracking-tight sm:text-3xl"
      >
        {title}
      </h2>
      {intro ? <p className="mt-2 max-w-3xl text-ink-soft">{intro}</p> : null}
      <div className="mt-6">{children}</div>
    </section>
  );
}

/** Step 4: the engine's decision, the three strategies, every outcome, and what is still open. */
export function CompareScreen({
  comparison,
  answers,
}: {
  comparison: Comparison;
  answers: Answers;
}) {
  const { field, decision, preview, analysisId, provenance, profile } = comparison;
  const ledger = buildEvidenceLedger(decision, profile, { preview });
  const answerParams = serializeAnswers(answers);

  const togglePreview = new URLSearchParams(answerParams);
  if (!preview) togglePreview.set("preview", "sample");

  const planParams = new URLSearchParams(answerParams);
  if (preview) planParams.set("preview", "sample");

  const priorityReadings = readPriorities(decision);

  return (
    <>
      <header>
        <h1 className="font-display text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
          Compare the options
        </h1>
        <p className="mt-3 text-lg text-ink-soft">
          {fieldName(field)}, {field.county} County ·{" "}
          {boundarySourceLabel[field.boundarySource]}
        </p>
      </header>

      <div className="mt-8 space-y-6">
        <PreviewNotice
          active={preview}
          missingIndicators={hasMissingIndicators(decision)}
          connected={apiBaseUrl() !== undefined}
          toggleHref={compareRoute(field.id, togglePreview)}
        />
        <EngineNotice provenance={provenance} />
        <OutcomeBanner decision={decision} />

        <dl className="grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-3">
          <Fact term="Crop history" className="sm:col-span-2">
            {decision.crop_history_summary}{" "}
            <span className="text-ink-faint">({fieldClassLabel[field.fieldClass]})</span>
          </Fact>
          <Fact term="Your answers">
            {countAnswered(answers)} of {TOTAL_QUESTIONS}.{" "}
            <Link
              href={prioritiesRoute(field.id, answerParams)}
              className="-my-3 inline-block py-3 font-semibold text-forest-700 underline underline-offset-4"
            >
              Change them
            </Link>
          </Fact>
        </dl>
      </div>

      <Block
        id="options"
        title="The three options side by side"
        intro="They are shown in the order of the rotation length, not from best to worst. Nothing here ranks them."
      >
        <StrategyCards decision={decision} />
      </Block>

      <Block
        id="basis"
        title="What this comparison rests on"
        intro="Evidence is not all alike. Here it is sorted by whose land it is about, from your own field down to what is only assumed. Read this before the figures."
      >
        <EvidenceLedger ledger={ledger} />
      </Block>

      <Block
        id="evidence"
        title="What the evidence says, one outcome at a time"
        intro="Each line says what kind of evidence it is, what it cannot tell you, and whether it applies to your farm. Things we cannot assess are shown, not hidden."
      >
        <div className="space-y-6">
          <PrioritiesPanel readings={priorityReadings} />
          <OutcomeCards
            decision={decision}
            highlighted={highlightedOutcomeIds(decision)}
          />
        </div>
      </Block>

      <Block
        id="open"
        title="Still open"
        intro="These would change what we can say. Some only you can answer; the rest need data we have not loaded."
      >
        <OpenQuestions
          fieldId={field.id}
          unknowns={decision.unknowns}
          answers={answers}
        />
      </Block>

      <Block id="limits" title="The limits of this comparison">
        <Limits limitations={decision.limitations} />
        <p className="mt-4 text-sm text-ink-faint">{engineLine(provenance)}</p>
      </Block>

      {analysisId ? (
        <AskPanel contextType="analysis" contextId={analysisId} action={askAnalysis} />
      ) : null}

      <nav
        aria-label="Next steps"
        className="mt-14 flex flex-wrap gap-3 border-t border-line pt-8"
      >
        <ButtonLink href={planRoute(field.id, planParams)}>
          Make a brief for my adviser
        </ButtonLink>
        <ButtonLink href={prioritiesRoute(field.id, answerParams)} variant="secondary">
          Change my answers
        </ButtonLink>
        <ButtonLink href={profileRoute(field.id)} variant="ghost">
          Back to the field profile
        </ButtonLink>
        <ButtonLink href={fieldRoute(field.id)} variant="ghost">
          Choose a different field
        </ButtonLink>
      </nav>
    </>
  );
}

function Fact({
  term,
  children,
  className,
}: {
  term: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`bg-surface px-5 py-4 ${className ?? ""}`}>
      <dt className="font-mono text-xs font-medium tracking-wide text-ink-faint uppercase">
        {term}
      </dt>
      <dd className="mt-1 text-[0.9375rem]">{children}</dd>
    </div>
  );
}
