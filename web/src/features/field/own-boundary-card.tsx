/** Draw and upload are planned, not built. Shown honestly as unavailable. */
export function OwnBoundaryCard({ highlight }: { highlight: boolean }) {
  const disabled =
    "inline-flex min-h-11 cursor-not-allowed items-center justify-center rounded-full border border-line px-5 text-sm font-semibold text-ink-faint";
  return (
    <section
      aria-labelledby="own-boundary-title"
      className={`rounded-[var(--radius-card)] border border-dashed p-6 ${highlight ? "border-harvest-500 bg-harvest-100/50" : "border-line-strong"}`}
    >
      <h2 id="own-boundary-title" className="font-semibold">
        Use your own boundary
      </h2>
      <p className="mt-1 text-[0.9375rem] text-ink-soft">
        Drawing or uploading a boundary inside Story or Boone County is not available in
        this build yet. The demonstration fields show the whole journey in the meantime.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        <span aria-disabled="true" className={disabled}>
          Draw boundary
        </span>
        <span aria-disabled="true" className={disabled}>
          Upload boundary file
        </span>
      </div>
    </section>
  );
}
