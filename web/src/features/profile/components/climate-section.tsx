import type { ClimateProfile, SectionStatus } from "../types";
import { IndicatorCard } from "./indicator-card";
import { SectionShell } from "./section-shell";

export function ClimateSection({
  status,
  data,
}: {
  status: SectionStatus;
  data: ClimateProfile;
}) {
  return (
    <SectionShell
      id="climate"
      title="The weather here"
      intro="From NASA weather data for an area about 50 km across around the field. It is your area's weather, not a weather station on your field."
      status={status}
      sampleNote="The weather pipeline is not connected yet, so these four numbers are not from NASA POWER. Do not use them."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {data.indicators.map((indicator) => (
          <IndicatorCard key={indicator.id} indicator={indicator} status={status} />
        ))}
      </div>
    </SectionShell>
  );
}
