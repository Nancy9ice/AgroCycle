import Link from "next/link";

interface PreviewNoticeProps {
  active: boolean;
  /** Link that turns the preview on or off while keeping the answers. */
  toggleHref: string;
}

/**
 * Says what is and is not real. No required indicator is computed for any field yet, so the
 * honest result is abstention; the preview lets reviewers see the rest of the screen.
 */
export function PreviewNotice({ active, toggleHref }: PreviewNoticeProps) {
  if (active) {
    return (
      <div
        role="note"
        className="rounded-2xl border border-harvest-500 bg-harvest-100 p-5 text-[0.9375rem]"
      >
        <p className="font-semibold text-harvest-700">
          Preview with sample values. This is not your field’s result.
        </p>
        <p className="mt-1 text-ink-soft">
          Weather, growing season and soil organic matter are not measured for this field
          yet, so this preview pretends they are known and fine. The crop history, your
          answers and the Iowa trial figures are real. Do not use this result to decide
          anything.
        </p>
        <Link
          href={toggleHref}
          className="mt-3 inline-block font-semibold text-forest-700 underline underline-offset-4"
        >
          Show the real result instead
        </Link>
      </div>
    );
  }
  return (
    <div
      role="note"
      className="rounded-2xl border border-line bg-surface p-5 text-[0.9375rem]"
    >
      <p className="font-semibold">Why is every field “not enough evidence” right now?</p>
      <p className="mt-1 text-ink-soft">
        The comparison needs four measurements for the field (growing-season heat,
        rainfall, frost-free days and soil organic matter). They are not calculated yet,
        and we do not treat missing data as good news.
      </p>
      <Link
        href={toggleHref}
        className="mt-3 inline-block font-semibold text-forest-700 underline underline-offset-4"
      >
        See what the screen looks like with sample values
      </Link>
    </div>
  );
}
