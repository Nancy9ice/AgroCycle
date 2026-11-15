/**
 * Shown for fields that are not a corn–soybean rotation. For a demonstration field it is an edge case on purpose;
 * for a boundary the farmer drew it is their own answer, and the wording must not call it a test.
 */
export function EdgeCaseNote({ className, own }: { className?: string; own?: boolean }) {
  return (
    <p
      role="note"
      className={`rounded-2xl bg-clay-100 px-4 py-3 text-[0.9375rem] text-clay-700 ${className ?? ""}`}
    >
      {own ? (
        <>
          <strong className="font-semibold">Outside what AgroCycle covers.</strong> From
          what you told us, this field is not a maize–soybean rotation, which is what
          AgroCycle is built for. Expect “not enough evidence” rather than a comparison.
        </>
      ) : (
        <>
          <strong className="font-semibold">An edge case on purpose.</strong> This field
          is not a maize–soybean rotation, which is what AgroCycle is built for. Use it to
          see how the tool handles a field the evidence does not cover. It is expected to
          say “not enough evidence” rather than compare the options.
        </>
      )}
    </p>
  );
}
