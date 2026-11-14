"use client";

import { AnswersSummary } from "./components/answers-summary";
import { QuestionField } from "./components/question-field";
import { constraintQuestions, priorityQuestions } from "./questions";
import { useAnswers } from "./use-answers";

/** Step 3: every question optional, answers kept in the URL. */
export function PrioritiesForm({ fieldId }: { fieldId: string }) {
  const { answers, setAnswer } = useAnswers();

  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-12">
      <form
        aria-label="Priorities and constraints"
        onSubmit={(event) => event.preventDefault()}
        className="space-y-12"
      >
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
