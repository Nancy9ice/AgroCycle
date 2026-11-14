"use client";

import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { counties, demoFields } from "./data";
import { FieldList } from "./field-list";
import { FieldMap, type CountyFilter } from "./field-map";
import { FieldSummaryPanel } from "./field-summary-panel";
import { OwnBoundaryCard } from "./own-boundary-card";
import { useSelectedField } from "./use-selected-field";

/** Step 1: the map, the list and the validation panel, kept in sync through the URL. */
export function FieldSelection() {
  const { selected, select, unknownRequestedId } = useSelectedField();
  const [countyFilter, setCountyFilter] = useState<CountyFilter>("all");
  const wantsOwnField = useSearchParams().get("mode") === "own";

  return (
    <div className="space-y-6">
      {unknownRequestedId ? (
        <p role="status" className="rounded-2xl bg-clay-100 px-4 py-3 text-clay-700">
          We could not find a field called “{unknownRequestedId}”, so the demo field is
          selected instead.
        </p>
      ) : null}

      <div className="grid gap-8 lg:grid-cols-[minmax(0,24rem)_minmax(0,1fr)] lg:gap-10">
        <div className="space-y-6 lg:col-start-2 lg:row-start-1">
          <FieldMap
            fields={demoFields}
            counties={counties}
            selectedId={selected.id}
            countyFilter={countyFilter}
            onSelect={select}
            className="h-[22rem] sm:h-[30rem]"
          />
          <FieldSummaryPanel field={selected} />
          <OwnBoundaryCard highlight={wantsOwnField} />
        </div>

        <div className="lg:col-start-1 lg:row-start-1">
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
