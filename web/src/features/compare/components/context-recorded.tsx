import type { ContextAnswers } from "../engine-input";
import { hasContext } from "../engine-input";

const yesNo = (value: boolean | null, yes: string, no: string) =>
  value === null ? "Not given" : value ? yes : no;

const labour = { little: "Little", some: "Some", plenty: "Plenty" } as const;

/**
 * The answers the rules do not read yet: hay equipment, storage and extra labour. They are shown so the farmer
 * can see they were kept, with the reason they do not change the result.
 */
export function ContextRecorded({
  context,
  note,
}: {
  context: ContextAnswers | undefined;
  note: string | undefined;
}) {
  if (!hasContext(context) || !context) return null;
  return (
    <section
      aria-labelledby="context-title"
      className="rounded-2xl border border-line bg-surface px-5 py-4"
    >
      <h2 id="context-title" className="text-sm font-semibold">
        Also recorded for your adviser
      </h2>
      <dl className="mt-2 grid gap-x-8 gap-y-1 text-[0.9375rem] sm:grid-cols-3">
        <div>
          <dt className="text-ink-faint">Hay equipment</dt>
          <dd className="font-semibold">
            {yesNo(context.hay_equipment_or_contractor, "Have or can hire", "No")}
          </dd>
        </div>
        <div>
          <dt className="text-ink-faint">Storage space</dt>
          <dd className="font-semibold">{yesNo(context.storage_space, "Yes", "No")}</dd>
        </div>
        <div>
          <dt className="text-ink-faint">Extra help at busy times</dt>
          <dd className="font-semibold">
            {context.extra_labour ? labour[context.extra_labour] : "Not given"}
          </dd>
        </div>
      </dl>
      {note ? <p className="mt-2 text-sm text-ink-soft">{note}</p> : null}
    </section>
  );
}
