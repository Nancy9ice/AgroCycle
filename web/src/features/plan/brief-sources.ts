import type { FieldProfile, Provenance } from "@/features/profile/types";

export interface BriefSource {
  /** What it is used for, e.g. "Crop history". */
  use: string;
  source: string;
  /** Product, version and retrieval date as far as the data layer recorded them. */
  detail: string;
}

/**
 * The sources and versions behind a field's profile, for the adviser brief. Only sections with real data
 * are listed: sample values are not a source, and listing them would make them look like one.
 */
export function profileSources(profile: FieldProfile | undefined): BriefSource[] {
  if (!profile) return [];
  const entries: Array<[string, Provenance | null | undefined, boolean]> = [
    [
      "Crop history",
      profile.cropHistory.provenance,
      profile.cropHistory.status === "available",
    ],
    ["Soil", profile.soil.provenance, profile.soil.status === "available"],
    [
      "Greenness",
      profile.vegetation.provenance,
      profile.vegetation.status === "available",
    ],
    ...(profile.climate.status === "available"
      ? (profile.climate.data?.indicators ?? []).map(
          (indicator): [string, Provenance, boolean] => [
            indicator.label,
            indicator.provenance,
            true,
          ],
        )
      : []),
  ];

  const seen = new Set<string>();
  const out: BriefSource[] = [];
  for (const [use, provenance, available] of entries) {
    if (!available || !provenance) continue;
    const { technical } = provenance;
    const detail = [
      technical.product,
      technical.version,
      technical.retrieved && `retrieved ${technical.retrieved}`,
    ]
      .filter(Boolean)
      .join(", ");
    const key = `${provenance.source}|${detail}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ use, source: provenance.source, detail: detail || "No version recorded" });
  }
  return out;
}

/** "2015 to 2025", or undefined when the history is not loaded. */
export function cropHistoryPeriod(profile: FieldProfile | undefined): string | undefined {
  const years = profile?.cropHistory.data?.years;
  if (!years || years.length === 0) return undefined;
  return `${years[0].year} to ${years[years.length - 1].year}`;
}
