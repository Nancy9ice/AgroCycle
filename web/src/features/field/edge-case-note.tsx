/** Shown for fields that are not a corn–soybean rotation (an edge case on purpose). */
export function EdgeCaseNote({ className }: { className?: string }) {
  return (
    <p
      role="note"
      className={`rounded-2xl bg-clay-100 px-4 py-3 text-[0.9375rem] text-clay-700 ${className ?? ""}`}
    >
      <strong className="font-semibold">An edge case on purpose.</strong> This field is
      not a maize–soybean rotation, which is what AgroCycle is built for. Use it to see
      how the tool handles a field the evidence does not cover. It is expected to say “not
      enough evidence” rather than compare the options.
    </p>
  );
}
