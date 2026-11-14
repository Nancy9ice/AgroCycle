import { questions, type Answers } from "./questions";

/**
 * Answers travel in the URL (`?manure=no&soil=high`) so a result can be shared and survives a
 * reload. URLs can be edited by hand, so parsing keeps only known questions with known option
 * values, and the first occurrence of a repeated key.
 */
export function parseAnswers(params: URLSearchParams): Answers {
  const answers: Record<string, string> = {};
  for (const question of questions) {
    const value = params.get(question.id);
    if (value !== null && question.options.some((option) => option.value === value)) {
      answers[question.id] = value;
    }
  }
  return answers;
}

/** The answered questions as query parameters, in question order, with unanswered ones omitted. */
export function serializeAnswers(answers: Answers): URLSearchParams {
  const params = new URLSearchParams();
  for (const question of questions) {
    const value = answers[question.id];
    if (value !== undefined) params.set(question.id, value);
  }
  return params;
}

export const countAnswered = (answers: Answers): number =>
  questions.filter((question) => answers[question.id] !== undefined).length;
