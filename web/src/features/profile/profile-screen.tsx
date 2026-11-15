import { PageHeader } from "@/components/layout/page-header";
import { ButtonLink } from "@/components/ui/button";
import { EdgeCaseNote } from "@/features/field/edge-case-note";
import { boundarySourceLabel, fieldName, isInDomain } from "@/features/field/labels";
import type { DemoField } from "@/features/field/types";
import { AskPanel } from "@/features/ask/ask-panel";
import { askField } from "@/features/ask/actions";
import { fieldRoute, prioritiesRoute } from "@/lib/routes";
import { AvailabilityStrip } from "./components/availability-strip";
import { ClimateSection } from "./components/climate-section";
import { CropHistorySection } from "./components/crop-history-section";
import { ProfileUiProvider } from "./components/profile-ui";
import { SoilSection } from "./components/soil-section";
import { VegetationSection } from "./components/vegetation-section";
import { ViewToggle } from "./components/view-toggle";
import type { FieldProfile } from "./types";

/** Step 2: everything we know about the selected field, each part labelled for what it is. */
export function ProfileScreen({
  field,
  profile,
}: {
  field: DemoField;
  profile: FieldProfile;
}) {
  const { cropHistory, climate, vegetation, soil } = profile;

  return (
    <ProfileUiProvider>
      <PageHeader
        title="What we know about this field"
        back={{ href: fieldRoute(field.id), label: "field selection" }}
        aside={<ViewToggle />}
      >
        <p>
          {fieldName(field)} · {field.county} County, Iowa · {field.areaHa.toFixed(1)} ha
          · {boundarySourceLabel[field.boundarySource]}, not a real farm.
        </p>
        <p className="text-ink-faint">
          Every number says what it is and where it came from.
        </p>
      </PageHeader>

      <div className="mt-6 space-y-8">
        {!isInDomain(field) ? <EdgeCaseNote /> : null}

        <AvailabilityStrip profile={profile} />

        {cropHistory.data ? (
          <CropHistorySection
            status={cropHistory.status}
            data={cropHistory.data}
            provenance={cropHistory.provenance}
          />
        ) : null}
        {climate.data ? (
          <ClimateSection status={climate.status} data={climate.data} />
        ) : null}
        {vegetation.data ? (
          <VegetationSection
            status={vegetation.status}
            data={vegetation.data}
            provenance={vegetation.provenance}
          />
        ) : null}
        {soil.data ? (
          <SoilSection
            status={soil.status}
            data={soil.data}
            provenance={soil.provenance}
          />
        ) : null}
      </div>

      <AskPanel contextType="field" contextId={field.id} action={askField} />

      <nav
        aria-label="Next step"
        className="mt-12 flex flex-col-reverse gap-3 border-t border-line pt-8 sm:flex-row sm:justify-between"
      >
        <ButtonLink href={fieldRoute(field.id)} variant="secondary">
          Back to choosing a field
        </ButtonLink>
        <ButtonLink href={prioritiesRoute(field.id)}>
          Next: what matters to you
        </ButtonLink>
      </nav>
    </ProfileUiProvider>
  );
}
