import { PageHeader } from "@/components/layout/page-header";
import { ButtonLink } from "@/components/ui/button";
import { EdgeCaseNote } from "@/features/field/edge-case-note";
import {
  boundarySourceLabel,
  fieldName,
  isDrawn,
  isKnownEdgeCase,
} from "@/features/field/labels";
import type { DemoField } from "@/features/field/types";
import { AskPanel } from "@/features/ask/ask-panel";
import { askField } from "@/features/ask/actions";
import { fieldRoute, prioritiesRoute } from "@/lib/routes";
import { AvailabilityStrip } from "./components/availability-strip";
import { ClimateSection } from "./components/climate-section";
import { choicesFromLetters } from "./components/crop-choices";
import { CropHistoryForm } from "./components/crop-history-form";
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
  const drawn = isDrawn(field);

  return (
    <ProfileUiProvider>
      <PageHeader
        title="What we know about this field"
        back={{ href: fieldRoute(field.id), label: "field selection" }}
        aside={<ViewToggle />}
      >
        <p>
          {fieldName(field)} · {field.county} County, Iowa · {field.areaHa.toFixed(1)} ha
          · {boundarySourceLabel[field.boundarySource]}
          {drawn ? "." : ", not a real farm."}
        </p>
        <p className="text-ink-faint">
          Every number says what it is and where it came from.
        </p>
      </PageHeader>

      <div className="mt-6 space-y-8">
        {isKnownEdgeCase(field) ? <EdgeCaseNote own={drawn} /> : null}

        {drawn ? (
          <p role="note" className="rounded-2xl bg-sunken px-4 py-3 text-[0.9375rem]">
            <strong className="font-semibold">
              Nothing has been prepared for your boundary.
            </strong>{" "}
            We have not worked out its crop history, weather or soil, so they show as not
            loaded below. We never show another field’s numbers as yours. You can tell us
            what you grew, and the comparison will say what is still missing.
          </p>
        ) : null}

        <AvailabilityStrip profile={profile} />

        {drawn ? (
          <section
            aria-labelledby="your-crops-title"
            className="rounded-[var(--radius-card)] border border-line bg-surface p-5 sm:p-6"
          >
            <h2 id="your-crops-title" className="font-display text-xl font-semibold">
              {cropHistory.data ? "What you told us you grew" : "Tell us what you grew"}
            </h2>
            {cropHistory.data ? (
              <details className="mt-3">
                <summary className="cursor-pointer text-sm font-semibold text-forest-700">
                  Change my answers
                </summary>
                <div className="mt-4">
                  <CropHistoryForm
                    fieldId={field.id}
                    initial={choicesFromLetters(
                      cropHistory.data.years.map((y) => y.code),
                    )}
                  />
                </div>
              </details>
            ) : (
              <div className="mt-3">
                <CropHistoryForm fieldId={field.id} />
              </div>
            )}
          </section>
        ) : null}

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
