import { cn } from "@/lib/cn";
import type { FieldProfile, SectionStatus } from "../types";

const statusText: Record<SectionStatus, string> = {
  available: "Ready",
  sample: "Sample values",
  not_loaded: "Not loaded",
};

const statusStyle: Record<SectionStatus, string> = {
  available: "bg-forest-100 text-forest-800",
  sample: "bg-harvest-100 text-harvest-700",
  not_loaded: "border border-dashed border-clay-700/50 bg-clay-100/60 text-clay-700",
};

/** What information exists for this field, and how real each part is. */
export function AvailabilityStrip({ profile }: { profile: FieldProfile }) {
  const items: { label: string; status: SectionStatus }[] = [
    { label: "What was grown, 2015 to 2025", status: profile.cropHistory.status },
    { label: "Soil map", status: profile.soil.status },
    { label: "Weather", status: profile.climate.status },
    { label: "Satellite greenness", status: profile.vegetation.status },
    { label: "Soil moisture from space", status: "not_loaded" },
  ];
  return (
    <section aria-labelledby="availability-title">
      <h2 id="availability-title" className="text-sm font-semibold text-ink-soft">
        What information we have
      </h2>
      <ul className="mt-3 flex flex-wrap gap-2">
        {items.map((item) => (
          <li
            key={item.label}
            className="flex items-center gap-2.5 rounded-full border border-line bg-surface py-1.5 pr-1.5 pl-4 text-sm font-medium"
          >
            {item.label}
            <span
              className={cn(
                "rounded-full px-2.5 py-1 font-mono text-xs",
                statusStyle[item.status],
              )}
            >
              {statusText[item.status]}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
