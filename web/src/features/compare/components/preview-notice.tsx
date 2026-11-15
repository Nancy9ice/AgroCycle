import Link from "next/link";

interface PreviewNoticeProps {
  active: boolean;
  /** True when the engine lists a required measurement as unknown for this field. */
  missingIndicators: boolean;
  /** Link that turns the preview on or off while keeping the answers. */
  toggleHref: string;
}

/**
 * Says what is and is not real. A sample preview always gets its banner. Otherwise a note appears only
 * when a required measurement is actually missing for this field, so it never claims data is absent
 * when it is not.
 */
export function PreviewNotice({
  active,
  missingIndicators,
  toggleHref,
}: PreviewNoticeProps) {
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
          This preview replaces the field’s measurements (growing-season heat, rain,
          frost-free days and soil organic matter) with sample values that are known and
          fine, whatever the data says. The crop history, your answers and the Iowa trial
          figures are real. Do not use this result to decide anything.
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
  if (!missingIndicators) return null;
  return (
    <div
      role="note"
      className="rounded-2xl border border-line bg-surface p-5 text-[0.9375rem]"
    >
      <p className="font-semibold">Why does this say “not enough evidence”?</p>
      <p className="mt-1 text-ink-soft">
        The comparison needs four measurements for the field (growing-season heat,
        rainfall, frost-free days and soil organic matter). At least one is not available
        here, and we do not treat missing data as good news.
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
