import type { Provenance, SectionStatus, VegetationProfile } from "../types";
import { GreennessChart } from "./greenness-chart";
import { SectionShell } from "./section-shell";

interface Props {
  status: SectionStatus;
  data: VegetationProfile;
  provenance: Provenance | null;
}

export function VegetationSection({ status, data, provenance }: Props) {
  return (
    <SectionShell
      id="greenness"
      title="How green the field is through the year"
      intro="Measured from NASA satellite images of this field. Tall bars mean plants are growing; short bars mean the soil is mostly bare."
      status={status}
      provenance={provenance}
      sampleNote="The satellite pipeline is not connected yet, so this chart is not from NASA HLS images of this field."
    >
      <GreennessChart months={data.months} />

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <p className="rounded-2xl bg-sunken px-4 py-3 text-[0.9375rem]">
          <strong className="font-semibold">
            Why some months say “don&rsquo;t know”:{" "}
          </strong>
          {data.unknownReason}
        </p>
        <p className="rounded-2xl bg-forest-50 px-4 py-3 text-[0.9375rem]">
          <strong className="font-semibold">What this means: </strong>
          {data.interpretation}
        </p>
      </div>
      <p className="mt-4 text-sm text-ink-faint">
        {data.barePrinciple} Greenness is not yield and not a soil measurement.
      </p>
    </SectionShell>
  );
}
