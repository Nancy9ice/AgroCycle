import type { Provenance, SectionStatus, SoilProfile } from "../types";
import { NotLoaded } from "./not-loaded";
import { SectionShell } from "./section-shell";

interface Props {
  status: SectionStatus;
  data: SoilProfile;
  provenance: Provenance | null;
}

export function SoilSection({ status, data, provenance }: Props) {
  return (
    <SectionShell
      id="soil"
      title="The soil"
      intro="From USDA soil maps, not a soil test from this field."
      status={status}
      provenance={provenance}
    >
      <dl className="divide-y divide-line rounded-2xl border border-line bg-surface">
        <div className="grid gap-1 px-5 py-4 sm:grid-cols-[11rem_1fr] sm:gap-4">
          <dt className="text-sm font-medium text-ink-faint">Soil type (series)</dt>
          <dd className="font-display text-xl font-semibold">{data.series}</dd>
        </div>
        <div className="grid gap-1 px-5 py-4 sm:grid-cols-[11rem_1fr] sm:gap-4">
          <dt className="text-sm font-medium text-ink-faint">Map unit</dt>
          <dd>{data.mapUnit}</dd>
        </div>
        <div className="grid gap-1 px-5 py-4 sm:grid-cols-[11rem_1fr] sm:gap-4">
          <dt className="text-sm font-medium text-ink-faint">Where it was read</dt>
          <dd className="text-ink-soft">{data.samplingNote}</dd>
        </div>
        <div className="grid gap-2 px-5 py-4 sm:grid-cols-[11rem_1fr] sm:gap-4">
          <dt className="text-sm font-medium text-ink-faint">Not loaded yet</dt>
          <dd className="flex flex-wrap gap-2">
            {data.notLoaded.map((item) => (
              <NotLoaded key={item}>{item}</NotLoaded>
            ))}
          </dd>
        </div>
      </dl>
    </SectionShell>
  );
}
