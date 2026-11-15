"use client";

import { ButtonLink } from "@/components/ui/button";
import { compareRoute } from "@/lib/routes";
import { AnswersSummary } from "./components/answers-summary";
import { QuestionField } from "./components/question-field";
import { countAnswered, serializeAnswers } from "./answers-codec";
import {
  constraintQuestions,
  priorityQuestions,
  startingPointAnswers,
  TOTAL_QUESTIONS,
} from "./questions";
import { useAnswers } from "./use-answers";

/** Step 3: every question optional, answers kept in the URL. */
export function PrioritiesForm({ fieldId }: { fieldId: string }) {
  const { answers, setAnswer, replaceAnswers } = useAnswers();
  const anyAnswered = countAnswered(answers) > 0;

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_21rem] lg:gap-10">
      <div className="min-w-0">
        <form
          aria-label="Priorities and constraints"
          onSubmit={(event) => event.preventDefault()}
          className="space-y-8"
        >
          <section
            aria-labelledby="quick-title"
            className="flex flex-col gap-3 rounded-2xl border border-forest-200 bg-forest-50 p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="max-w-xl">
              <h2 id="quick-title" className="font-medium">
                Short on time?
              </h2>
              <p className="mt-0.5 text-[0.8125rem] text-ink-soft sm:text-sm">
                Fill in a starting point: “Medium” for what matters, “Not sure” for your
                farm. We never guess yes or no. Then change only what you know.
              </p>
            </div>
            <div className="flex shrink-0 flex-wrap gap-2">
              <button
                type="button"
                onClick={() => replaceAnswers(startingPointAnswers())}
                className="inline-flex min-h-11 items-center justify-center rounded-full border border-forest-700 bg-forest-700 px-4 text-sm font-medium text-white transition-colors hover:bg-forest-800"
              >
                Fill in a starting point
              </button>
              <button
                type="button"
                onClick={() => replaceAnswers({})}
                disabled={!anyAnswered}
                className="inline-flex min-h-11 items-center justify-center rounded-full border border-line-strong bg-surface px-4 text-sm font-medium transition-colors hover:border-forest-600 hover:bg-forest-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Clear all
              </button>
            </div>
          </section>

          <section aria-labelledby="matters-title" className="space-y-4">
            <div>
              <h2 id="matters-title" className="font-display text-xl font-medium">
                What matters to you
              </h2>
              <p className="mt-1 text-sm text-ink-soft sm:text-base">
                How much does each of these matter, for this field?
              </p>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {priorityQuestions.map((question) => (
                <QuestionField
                  key={question.id}
                  question={question}
                  value={answers[question.id]}
                  onChange={(value) => setAnswer(question.id, value)}
                />
              ))}
            </div>
          </section>

          <section aria-labelledby="possible-title" className="space-y-4">
            <div>
              <h2 id="possible-title" className="font-display text-xl font-medium">
                What is possible on your farm
              </h2>
              <p className="mt-1 text-sm text-ink-soft sm:text-base">
                These decide which comparisons fit your farm. “Not sure” is a fine answer.
              </p>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {constraintQuestions.map((question) => (
                <QuestionField
                  key={question.id}
                  question={question}
                  value={answers[question.id]}
                  onChange={(value) => setAnswer(question.id, value)}
                />
              ))}
            </div>
          </section>
        </form>

        {/* On a phone the summary is far below the questions, so the way on stays within reach. */}
        <div className="sticky bottom-3 z-10 mt-6 lg:hidden">
          <ButtonLink
            href={compareRoute(fieldId, serializeAnswers(answers))}
            className="min-h-12 w-full text-sm font-medium shadow-card"
          >
            Compare strategies · {countAnswered(answers)}/{TOTAL_QUESTIONS} answered
          </ButtonLink>
        </div>
      </div>

      <div className="lg:sticky lg:top-24 lg:self-start">
        <AnswersSummary fieldId={fieldId} answers={answers} />
      </div>
    </div>
  );
}
