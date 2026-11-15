"use client";

import { useState } from "react";
import { counties, demoFields } from "./data";
import { FieldList } from "./field-list";
import { FieldMap, type CountyFilter } from "./field-map";
import { FieldSummaryPanel } from "./field-summary-panel";
import { useSelectedField } from "./use-selected-field";

/**
 * Pick a demo field. The map is the main thing: it fills the left and the field you choose appears on
 * the right with its one next step. The list is a scrolling picker, not a page-long column.
 * Map, list and summary stay in sync through the URL.
 */
export function FieldSelection() {
  const { selected, select, unknownRequestedId } = useSelectedField();
  const [countyFilter, setCountyFilter] = useState<CountyFilter>("all");

  return (
    <div className="space-y-4">
      {unknownRequestedId ? (
        <p role="status" className="rounded-2xl bg-clay-100 px-4 py-3 text-clay-700">
          We could not find a field called “{unknownRequestedId}”, so the demo field is
          selected instead.
        </p>
      ) : null}

      <div className="grid gap-6 lg:h-[calc(100dvh-17rem)] lg:min-h-[34rem] lg:grid-cols-[minmax(0,1fr)_minmax(0,26rem)]">
        <FieldMap
          fields={demoFields}
          counties={counties}
          selectedId={selected.id}
          countyFilter={countyFilter}
          onSelect={select}
          className="h-[22rem] sm:h-[28rem] lg:h-auto lg:min-h-[17rem] lg:flex-1"
        />

        <div className="flex min-h-0 flex-col gap-4">
          <FieldSummaryPanel field={selected} />
          <div className="flex min-h-0 flex-1 flex-col rounded-[var(--radius-card)] border border-line bg-surface p-3 shadow-card">
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
    </div>
  );
}
