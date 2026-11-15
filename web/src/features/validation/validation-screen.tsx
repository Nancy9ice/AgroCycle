import { PageHeader } from "@/components/layout/page-header";
import { cn } from "@/lib/cn";
import { routes } from "@/lib/routes";
import {
  SNAPSHOT_DATE,
  checkKinds,
  countByKind,
  unreconciled,
  validationRows,
  type CheckState,
  type ValidationRow,
} from "./content";

const stateLabel: Record<CheckState, string> = {
  done: "Done",
  partly: "Partly",
  none: "Not done",
};

const stateGlyph: Record<CheckState, string> = { done: "✓", partly: "◐", none: "–" };

const stateStyle: Record<CheckState, string> = {
  done: "border-forest-200 bg-forest-100 text-forest-800",
  partly: "border-harvest-500/50 bg-harvest-100 text-harvest-700",
  none: "border-line-strong bg-sunken text-ink-faint",
};

/** `/validation`: what has been checked, by what kind of check, and what has not. */
export function ValidationScreen() {
  const counts = countByKind(validationRows);

  return (
    <>
      <PageHeader
        eyebrow="Honest answers"
        title="How we checked this"
        back={{ href: routes.home, label: "home" }}
      >
        <p>
          “Tested” and “right” are different things. For each part of AgroCycle, this page
          shows what has been checked, by which of four kinds of check, and what has not
          been checked at all. Gaps are shown, not hidden.
        </p>
        <p className="text-sm text-ink-faint">
          A snapshot taken {SNAPSHOT_DATE} from the project’s own test records. Counts and
          results are as recorded there, not re-run for this page.
        </p>
      </PageHeader>

      <section aria-labelledby="kinds-title" className="mt-12">
        <h2 id="kinds-title" className="font-display text-2xl font-semibold">
          Four kinds of check
        </h2>
        <p className="mt-2 max-w-3xl text-ink-soft">
          They are kept apart on purpose. Passing our own tests never counts as being
          independently confirmed.
        </p>
        <dl className="mt-6 grid gap-4 sm:grid-cols-2">
          {checkKinds.map((kind) => {
            const count = counts[kind.id];
            return (
              <div
                key={kind.id}
                className="rounded-[var(--radius-card)] border border-line bg-surface p-5"
              >
                <dt className="font-semibold">{kind.label}</dt>
                <dd className="mt-1 text-[0.9375rem] text-ink-soft">{kind.meaning}</dd>
                <dd className="mt-3 font-mono text-sm">
                  <span className="font-semibold">{count.done}</span> of {count.total}{" "}
                  done
                  {count.partly > 0 ? <>, {count.partly} partly</> : null}
                </dd>
              </div>
            );
          })}
        </dl>
      </section>

      <section aria-labelledby="unreconciled-title" className="mt-12">
        <div
          role="note"
          className="rounded-[var(--radius-card)] border-l-8 border-clay-700 bg-clay-100/60 p-6"
        >
          <h2 id="unreconciled-title" className="font-display text-2xl font-semibold">
            {unreconciled.title}
          </h2>
          <p className="mt-2 max-w-3xl text-[0.9375rem]">{unreconciled.body}</p>
          <p className="mt-3 font-mono text-xs text-ink-faint">{unreconciled.source}</p>
        </div>
      </section>

      <section aria-labelledby="rows-title" className="mt-12">
        <h2 id="rows-title" className="font-display text-2xl font-semibold">
          Part by part
        </h2>
        <ol className="mt-6 space-y-5">
          {validationRows.map((row, index) => (
            <li key={row.id}>
              <RowCard row={row} number={index + 1} />
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="meaning-title" className="mt-12">
        <h2 id="meaning-title" className="font-display text-2xl font-semibold">
          What this means for the results you see
        </h2>
        <ul className="mt-4 max-w-3xl list-disc space-y-2 pl-5 text-ink-soft">
          <li>
            Where a measurement the comparison needs is missing for a field, or the field
            is not a corn–soybean rotation, the comparison says “not enough evidence”. We
            would rather say that than guess.
          </li>
          <li>
            Where the app shows sample values (greenness today, and weather when it runs
            without the data service), it says so on the page.
          </li>
          <li>
            Nothing here is a reason to change a rotation. It is a way to decide what to
            ask someone who knows your land.
          </li>
        </ul>
      </section>
    </>
  );
}

function RowCard({ row, number }: { row: ValidationRow; number: number }) {
  const headingId = `row-${row.id}`;
  return (
    <article
      aria-labelledby={headingId}
      className="rounded-[var(--radius-card)] border border-line bg-surface p-5 sm:p-6"
    >
      <header className="flex flex-wrap items-start justify-between gap-3">
        <h3 id={headingId} className="text-lg font-semibold">
          <span className="mr-2 font-mono text-sm text-ink-faint">{number}</span>
          {row.component}
        </h3>
        <ul aria-label="Kinds of check" className="flex flex-wrap gap-2">
          {checkKinds.map((kind) => (
            <li
              key={kind.id}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
                stateStyle[row.kinds[kind.id]],
              )}
            >
              <span aria-hidden className="font-mono">
                {stateGlyph[row.kinds[kind.id]]}
              </span>
              {kind.label}: {stateLabel[row.kinds[kind.id]]}
            </li>
          ))}
        </ul>
      </header>

      <dl className="mt-4 grid gap-x-8 gap-y-3 sm:grid-cols-[9rem_1fr]">
        <dt className="text-sm font-semibold">What was checked</dt>
        <dd className="text-[0.9375rem]">{row.checked}</dd>
        <dt className="text-sm font-semibold">What we found</dt>
        <dd className="text-[0.9375rem]">{row.result}</dd>
        <dt className="text-sm font-semibold">What it does not show</dt>
        <dd className="text-[0.9375rem] text-ink-soft">{row.doesNotShow}</dd>
        <dt className="text-sm font-semibold">Record</dt>
        <dd className="font-mono text-xs break-words text-ink-faint">{row.source}</dd>
      </dl>
    </article>
  );
}
