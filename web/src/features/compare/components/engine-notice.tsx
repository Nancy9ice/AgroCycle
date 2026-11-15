import type { ComparisonProvenance } from "../get-comparison";

/**
 * Says which engine produced the result. The AgroCycle service is the authoritative one; the copy of the
 * rules inside the website is for running with no backend and must never pass for the service. Shown only
 * when the offline copy answered.
 */
export function EngineNotice({ provenance }: { provenance: ComparisonProvenance }) {
  if (provenance.source === "api") return null;
  return (
    <div
      role="note"
      className="rounded-2xl border border-harvest-500 bg-harvest-100 p-5 text-[0.9375rem]"
    >
      <p className="font-semibold text-harvest-700">
        Offline copy of the rules. This did not come from the AgroCycle service.
      </p>
      <p className="mt-1 text-ink-soft">
        This site could not ask the service, so it ran a copy of the rules built into the
        website. The copy follows the same rules, but it cannot see this field’s weather
        or drainage. Use it to see how the screens work, not to learn about a field.
      </p>
    </div>
  );
}

const sourceLabel: Record<ComparisonProvenance["source"], string> = {
  api: "the AgroCycle service",
  offline_fallback: "an offline copy of the rules inside the website (not the service)",
};

/** The same facts as one plain sentence, for the foot of the compare screen and the brief. */
export function engineLine(provenance: ComparisonProvenance): string {
  const parts = [
    `Calculated by ${sourceLabel[provenance.source]}`,
    `rules version ${provenance.rulesVersion}`,
    provenance.dataVersion ? `data version ${provenance.dataVersion}` : "no data version",
  ];
  if (provenance.createdAt) parts.push(`run ${provenance.createdAt.slice(0, 10)}`);
  return `${parts.join(", ")}.`;
}
