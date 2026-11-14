import { crops } from "@/domain/crops";
import { cn } from "@/lib/cn";
import type { CropHistory, Provenance, SectionStatus } from "../types";
import { SectionShell } from "./section-shell";

interface Props {
  status: SectionStatus;
  data: CropHistory;
  provenance: Provenance | null;
}

export function CropHistorySection({ status, data, provenance }: Props) {
  const repeated = new Set(data.repeatedYears);
  return (
    <SectionShell
      id="crop-history"
      title="What was grown each year"
      intro={data.summary}
      status={status}
      provenance={provenance}
    >
      <ol className="grid grid-cols-4 gap-2 sm:grid-cols-6 lg:grid-cols-11">
        {data.years.map(({ year, code }) => {
          const crop = crops[code];
          return (
            <li key={year} className="flex flex-col gap-1.5">
              <span className="font-mono text-xs text-ink-faint">{year}</span>
              <span
                aria-hidden
                className={cn(
                  "h-12 rounded-xl",
                  crop.swatch,
                  repeated.has(year) &&
                    "ring-2 ring-ink ring-offset-2 ring-offset-surface",
                )}
              />
              <span className="text-sm leading-tight font-medium">
                {crop.label}
                {repeated.has(year) ? (
                  <span className="sr-only"> (same crop as the year before)</span>
                ) : null}
              </span>
            </li>
          );
        })}
      </ol>
      {data.repeatedYears.length > 0 ? (
        <p className="mt-4 text-sm text-ink-faint">
          Outlined years grew the same crop as the year before.
        </p>
      ) : null}
    </SectionShell>
  );
}
