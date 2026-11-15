"use client";

import { ChevronDownIcon } from "@/components/icons/chevron-down-icon";
import { useState } from "react";
import { cn } from "@/lib/cn";
import type { CountyFilter } from "./field-map";
import { fieldClassLabel, fieldName, isInDomain } from "./labels";
import type { DemoField } from "./types";

interface FieldListProps {
  fields: readonly DemoField[];
  selectedId: string;
  countyFilter: CountyFilter;
  onSelect: (id: string) => void;
  onCountyFilterChange: (filter: CountyFilter) => void;
}

const countyOptions: readonly { value: CountyFilter; label: string }[] = [
  { value: "all", label: "Both counties" },
  { value: "Story", label: "Story" },
  { value: "Boone", label: "Boone" },
];

function FieldItem({
  field,
  selected,
  onSelect,
}: {
  field: DemoField;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <li>
      <button
        type="button"
        aria-pressed={selected}
        onClick={() => onSelect(field.id)}
        className={cn(
          "flex w-full items-center justify-between gap-3 rounded-2xl border px-4 py-3 text-left transition-colors",
          selected
            ? "border-forest-600 bg-forest-50 ring-2 ring-forest-600/30"
            : "border-line bg-surface hover:border-forest-600/60 hover:bg-forest-50/60",
        )}
      >
        <span>
          <span className="block font-semibold">{fieldName(field)}</span>
          <span className="block text-sm text-ink-faint">
            {field.county} County · {field.areaHa.toFixed(1)} ha
            {isInDomain(field) ? "" : ` · ${fieldClassLabel[field.fieldClass]}`}
          </span>
        </span>
        {field.role === "primary" ? (
          <span className="shrink-0 rounded-full bg-harvest-100 px-2.5 py-1 font-mono text-xs font-medium text-harvest-700">
            Primary
          </span>
        ) : null}
      </button>
    </li>
  );
}

function GroupHeading({
  children,
  count,
}: {
  children: React.ReactNode;
  count?: number;
}) {
  return (
    <h3 className="flex items-baseline justify-between gap-3 px-1 text-sm font-semibold text-ink-soft">
      <span>{children}</span>
      {count !== undefined ? (
        <span className="font-mono text-xs font-medium text-ink-faint">{count}</span>
      ) : null}
    </h3>
  );
}

export function FieldList({
  fields,
  selectedId,
  countyFilter,
  onSelect,
  onCountyFilterChange,
}: FieldListProps) {
  const [edgeOpenByUser, setEdgeOpenByUser] = useState(false);

  const visible = fields.filter(
    (f) => countyFilter === "all" || f.county === countyFilter,
  );
  const primary = visible.filter((f) => f.role === "primary");
  const rotation = visible.filter((f) => f.role === "test" && isInDomain(f));
  const edge = visible.filter((f) => !isInDomain(f));

  // Keep the selected field visible: its group stays open while it is selected.
  const selectedIsEdge = edge.some((f) => f.id === selectedId);
  const edgeOpen = edgeOpenByUser || selectedIsEdge;

  return (
    <div className="space-y-6">
      <div
        role="group"
        aria-label="Show fields in"
        className="flex gap-1 rounded-full bg-sunken p-1"
      >
        {countyOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            aria-pressed={countyFilter === option.value}
            onClick={() => onCountyFilterChange(option.value)}
            className={cn(
              "min-h-11 flex-1 rounded-full px-3 text-sm font-semibold transition-colors",
              countyFilter === option.value
                ? "bg-surface text-forest-800 shadow-sm"
                : "text-ink-soft hover:text-ink",
            )}
          >
            {option.label}
          </button>
        ))}
      </div>

      {primary.length > 0 ? (
        <section aria-label="Primary demo field" className="space-y-2">
          <GroupHeading>Primary demo field</GroupHeading>
          <ul className="space-y-2">
            {primary.map((field) => (
              <FieldItem
                key={field.id}
                field={field}
                selected={field.id === selectedId}
                onSelect={onSelect}
              />
            ))}
          </ul>
        </section>
      ) : null}

      <section aria-label="Test fields" className="space-y-2">
        <GroupHeading count={rotation.length}>
          Test fields (corn–soybean rotation)
        </GroupHeading>
        <ul className="space-y-2">
          {rotation.map((field) => (
            <FieldItem
              key={field.id}
              field={field}
              selected={field.id === selectedId}
              onSelect={onSelect}
            />
          ))}
        </ul>
      </section>

      <section aria-label="Edge-case fields" className="space-y-2">
        <button
          type="button"
          aria-expanded={edgeOpen}
          aria-disabled={selectedIsEdge}
          onClick={() => setEdgeOpenByUser((open) => !open)}
          className="flex min-h-11 w-full items-center justify-between gap-3 rounded-2xl border border-dashed border-line-strong px-4 py-2 text-left text-sm font-semibold text-ink-soft hover:bg-surface"
        >
          <span>
            Edge cases
            <span className="block text-xs font-normal text-ink-faint">
              Not a corn–soybean field, so we expect “not enough evidence”
            </span>
          </span>
          <span className="flex items-center gap-2 font-mono text-xs text-ink-faint">
            {edge.length}
            <ChevronDownIcon
              className={cn("size-4 transition-transform", edgeOpen && "rotate-180")}
            />
          </span>
        </button>
        {edgeOpen ? (
          <ul className="space-y-2">
            {edge.map((field) => (
              <FieldItem
                key={field.id}
                field={field}
                selected={field.id === selectedId}
                onSelect={onSelect}
              />
            ))}
          </ul>
        ) : null}
      </section>
    </div>
  );
}
