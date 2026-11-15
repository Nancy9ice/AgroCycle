"use client";

import { useState } from "react";
import { FieldList } from "./field-list";
import { FieldMap, type CountyFilter } from "./field-map";
import { FieldSummaryPanel } from "./field-summary-panel";
import type { County, DemoField } from "./types";
import { useSelectedField } from "./use-selected-field";

/** Step 1: the map, the list and the validation panel, kept in sync through the URL. */
export function FieldSelection({
  fields: demoFields,
  counties,
}: {
  fields: readonly DemoField[];
  counties: readonly County[];
}) {
  const { selected, select, unknownRequestedId } = useSelectedField(demoFields);
  const [countyFilter, setCountyFilter] = useState<CountyFilter>("all");

  return (
    <div className="space-y-6">
      {unknownRequestedId ? (
        <p role="status" className="rounded-2xl bg-clay-100 px-4 py-3 text-clay-700">
          We could not find a field called “{unknownRequestedId}”, so the demo field is
          selected instead.
        </p>
      ) : null}

      <div className="grid gap-8 lg:grid-cols-[minmax(0,24rem)_minmax(0,1fr)] lg:gap-10">
        {/* Right column: stays in view on desktop while the list scrolls. */}
        <div className="flex flex-col gap-4 lg:sticky lg:top-24 lg:col-start-2 lg:row-start-1 lg:h-[calc(100dvh-7rem)] lg:self-start">
          <FieldMap
            fields={demoFields}
            counties={counties}
            selectedId={selected.id}
            countyFilter={countyFilter}
            onSelect={select}
            className="h-[22rem] sm:h-[30rem] lg:h-auto lg:min-h-[17rem] lg:flex-1"
          />
          <FieldSummaryPanel field={selected} counties={counties} />
        </div>

        <div className="space-y-8 lg:col-start-1 lg:row-start-1">
          <h2 className="sr-only">All demonstration fields</h2>
          <FieldList
            fields={demoFields}
            selectedId={selected.id}
            countyFilter={countyFilter}
            onSelect={select}
            onCountyFilterChange={setCountyFilter}
          />
        </div>
      </div>
    </div>
  );
}
