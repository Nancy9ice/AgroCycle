import Link from "next/link";
import { prioritiesRoute } from "@/lib/routes";
import type { Answers } from "@/features/priorities/questions";
import { serializeAnswers } from "@/features/priorities/answers-codec";
import { toOpenQuestions } from "../open-questions";

interface OpenQuestionsProps {
  fieldId: string;
  unknowns: readonly string[];
  answers: Answers;
}

/** The engine's unknowns as questions: the ones you can answer, and the data we do not have yet. */
export function OpenQuestions({ fieldId, unknowns, answers }: OpenQuestionsProps) {
  const items = toOpenQuestions(unknowns);
  const you = items.filter((item) => item.kind === "you");
  const data = items.filter((item) => item.kind === "data");

  if (items.length === 0) {
    return (
      <p className="rounded-2xl border border-line bg-surface p-5 text-ink-soft">
        Nothing the engine needs is unknown. That does not make the result certain: see
        the limits below.
      </p>
    );
  }

  return (
    <div className="grid gap-5 md:grid-cols-2">
      <section
        aria-labelledby="you-title"
        className="rounded-[var(--radius-card)] border border-line bg-surface p-6"
      >
        <h3 id="you-title" className="font-display text-xl font-semibold">
          Only you can answer these
        </h3>
        {you.length > 0 ? (
          <>
            <ul className="mt-3 list-disc space-y-2 pl-5">
              {you.map((item) => (
                <li key={item.key}>{item.text}</li>
              ))}
            </ul>
            <Link
              href={prioritiesRoute(fieldId, serializeAnswers(answers))}
              className="mt-4 inline-block font-semibold text-forest-700 underline underline-offset-4"
            >
              Answer them
            </Link>
          </>
        ) : (
          <p className="mt-3 text-ink-soft">
            You have answered everything the comparison uses.
          </p>
        )}
      </section>

      <section
        aria-labelledby="data-title"
        className="rounded-[var(--radius-card)] border border-line bg-surface p-6"
      >
        <h3 id="data-title" className="font-display text-xl font-semibold">
          What we do not know about the field yet
        </h3>
        {data.length > 0 ? (
          <ul className="mt-3 list-disc space-y-2 pl-5">
            {data.map((item) => (
              <li key={item.key}>{item.text}</li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-ink-soft">Nothing missing that the comparison needs.</p>
        )}
      </section>
    </div>
  );
}
