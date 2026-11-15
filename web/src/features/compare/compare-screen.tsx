import { Suspense, type ReactNode } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/layout/page-header";
import { ButtonLink } from "@/components/ui/button";
import { apiBaseUrl } from "@/lib/api";
import { cn } from "@/lib/cn";
import { boundarySourceLabel, fieldClassLabel, fieldName } from "@/features/field/labels";
import { serializeAnswers } from "@/features/priorities/answers-codec";
import { countAnswered } from "@/features/priorities/answers-codec";
import { TOTAL_QUESTIONS, type Answers } from "@/features/priorities/questions";
import {
  analysisRoute,
  compareRoute,
  feedbackRoute,
  fieldRoute,
  planRoute,
  prioritiesRoute,
  profileRoute,
  routes,
} from "@/lib/routes";
import { AskPanel } from "@/features/ask/ask-panel";
import { SeasonSummary } from "@/features/season/season-summary";
import { askAnalysis } from "@/features/ask/actions";
import { ContextRecorded } from "./components/context-recorded";
import { EngineNotice, engineLine } from "./components/engine-notice";
import { EvidenceLedger } from "./components/evidence-ledger";
import { OpenQuestions } from "./components/open-questions";
import { Limits } from "./components/limits";
import { OutcomeBanner } from "./components/outcome-banner";
import { OutcomeCards } from "./components/outcome-cards";
import { PreviewNotice } from "./components/preview-notice";
import { PrioritiesPanel } from "./components/priorities-panel";
import { ShareLink } from "./components/share-link";
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
        className="font-display text-xl font-medium tracking-tight sm:text-2xl"
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
  const {
    field,
    decision,
    preview,
    analysisId,
    provenance,
    profile,
    context,
    contextNote,
    saved,
  } = comparison;
  const ledger = buildEvidenceLedger(decision, profile, { preview });
  const answerParams = serializeAnswers(answers);

  const togglePreview = new URLSearchParams(answerParams);
  if (!preview) togglePreview.set("preview", "sample");

  const planParams = new URLSearchParams(answerParams);
  if (preview) planParams.set("preview", "sample");

  const priorityReadings = readPriorities(decision);

  return (
    <>
      <PageHeader
        title={saved ? "Saved comparison" : "Compare the options"}
        back={{
          href: prioritiesRoute(field.id, new URLSearchParams(answerParams)),
          label: "your priorities",
        }}
      >
        <p>
          {fieldName(field)}, {field.county} County ·{" "}
          {boundarySourceLabel[field.boundarySource]}
        </p>
      </PageHeader>

      <div className="mt-6 space-y-6">
        <PreviewNotice
          active={preview}
          missingIndicators={hasMissingIndicators(decision)}
          connected={apiBaseUrl() !== undefined}
          toggleHref={compareRoute(field.id, togglePreview)}
        />
        {saved ? (
          <p
            role="note"
            className="rounded-2xl border border-line bg-sunken px-5 py-4 text-[0.9375rem]"
          >
            This is a saved result, shown exactly as it was run
            {provenance.createdAt
              ? ` on ${new Date(provenance.createdAt).toLocaleDateString("en-GB", { dateStyle: "long" })}`
              : ""}
            . It has not been run again, so it does not use any newer data.{" "}
            <Link
              href={prioritiesRoute(field.id)}
              className="font-semibold text-forest-700 underline underline-offset-4"
            >
              Run it again with your answers
            </Link>
          </p>
        ) : null}
        <EngineNotice provenance={provenance} />
        <OutcomeBanner decision={decision} />
        <ContextRecorded context={context} note={contextNote} />

        <dl className="grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-3">
          <Fact term="Crop history" className="sm:col-span-2">
            {decision.crop_history_summary}{" "}
            <span className="text-ink-faint">({fieldClassLabel[field.fieldClass]})</span>
          </Fact>
          <Fact term="Your answers">
            {saved ? (
              <>Kept with the saved result. </>
            ) : (
              <>
                {countAnswered(answers)} of {TOTAL_QUESTIONS}.{" "}
              </>
            )}
            <Link
              href={prioritiesRoute(field.id, answerParams)}
              className="-my-3 inline-block py-3 font-semibold text-forest-700 underline underline-offset-4"
            >
              {saved ? "Start again" : "Change them"}
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
        id="seasons"
        title="How past seasons looked in this field’s weather"
        intro="Hot days, dry spells, rain and warmth for each season on record. These are counts of past weather over a whole season. They do not say when in the season anything happened, and they are not a forecast or a yield estimate."
      >
        <Suspense fallback={<p className="text-ink-soft">Loading past seasons…</p>}>
          <SeasonSummary fieldId={field.id} />
        </Suspense>
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
        <p className="mt-2 text-sm">
          <Link
            href={routes.marsden}
            className="font-semibold text-forest-700 underline underline-offset-4"
          >
            Read about the experiment this rests on
          </Link>
          {" · "}
          <Link
            href={routes.methods}
            className="font-semibold text-forest-700 underline underline-offset-4"
          >
            Where the numbers come from
          </Link>
        </p>
      </Block>

      {analysisId ? (
        <AskPanel contextType="analysis" contextId={analysisId} action={askAnalysis} />
      ) : null}

      {/* Its own block: the link box it reveals grows, and in the button row it stretched every button. */}
      {analysisId ? (
        <div className="mt-14 border-t border-line pt-8">
          <ShareLink path={analysisRoute(analysisId)} />
        </div>
      ) : null}

      <nav
        aria-label="Next steps"
        className={cn(
          "flex flex-wrap items-start gap-3",
          analysisId ? "mt-6" : "mt-14 border-t border-line pt-8",
        )}
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
        <ButtonLink
          href={feedbackRoute({ fieldId: field.id, analysisId })}
          variant="ghost"
        >
          Give feedback
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
