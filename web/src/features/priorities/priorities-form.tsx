"use client";

import { AnswersSummary } from "./components/answers-summary";
import { QuestionField } from "./components/question-field";
import { countAnswered } from "./answers-codec";
import {
  constraintQuestions,
  priorityQuestions,
  startingPointAnswers,
} from "./questions";
import { useAnswers } from "./use-answers";

/** Step 3: every question optional, answers kept in the URL. */
export function PrioritiesForm({ fieldId }: { fieldId: string }) {
  const { answers, setAnswer, replaceAnswers } = useAnswers();
  const anyAnswered = countAnswered(answers) > 0;

  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-12">
      <form
        aria-label="Priorities and constraints"
        onSubmit={(event) => event.preventDefault()}
        className="space-y-12"
      >
        <section
          aria-labelledby="quick-title"
          className="rounded-[var(--radius-card)] border border-forest-200 bg-forest-50 p-5"
        >
          <h2 id="quick-title" className="font-semibold">
            Short on time?
          </h2>
          <p className="mt-1 text-[0.9375rem] text-ink-soft">
            We can fill in a starting point: “Medium” for what matters, and “Not sure” for
            the questions about your farm. We never guess yes or no about your farm. Then
            change only the answers you know.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => replaceAnswers(startingPointAnswers())}
              className="inline-flex min-h-12 items-center justify-center rounded-full border border-forest-700 bg-forest-700 px-5 text-[0.9375rem] font-semibold text-white transition-colors hover:bg-forest-800"
            >
              Fill in a starting point
            </button>
            <button
              type="button"
              onClick={() => replaceAnswers({})}
              disabled={!anyAnswered}
              className="inline-flex min-h-12 items-center justify-center rounded-full border border-line-strong bg-surface px-5 text-[0.9375rem] font-semibold transition-colors hover:border-forest-600 hover:bg-forest-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Clear all answers
            </button>
          </div>
        </section>

        <section aria-labelledby="matters-title" className="space-y-4">
          <div>
            <h2 id="matters-title" className="font-display text-2xl font-semibold">
              What matters to you
            </h2>
            <p className="mt-1 text-ink-soft">
              How much does each of these matter, for this field?
            </p>
          </div>
          {priorityQuestions.map((question) => (
            <QuestionField
              key={question.id}
              question={question}
              value={answers[question.id]}
              onChange={(value) => setAnswer(question.id, value)}
            />
          ))}
        </section>

        <section aria-labelledby="possible-title" className="space-y-4">
          <div>
            <h2 id="possible-title" className="font-display text-2xl font-semibold">
              What is possible on your farm
            </h2>
            <p className="mt-1 text-ink-soft">
              These decide which comparisons fit your farm. “Not sure” is a fine answer.
            </p>
          </div>
          {constraintQuestions.map((question) => (
            <QuestionField
              key={question.id}
              question={question}
              value={answers[question.id]}
              onChange={(value) => setAnswer(question.id, value)}
            />
          ))}
        </section>
      </form>

      <div className="lg:sticky lg:top-24 lg:self-start">
        <AnswersSummary fieldId={fieldId} answers={answers} />
      </div>
    </div>
  );
}
