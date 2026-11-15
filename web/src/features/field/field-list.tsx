"use client";

import { ChevronDownIcon } from "@/components/icons/chevron-down-icon";
import { useEffect, useRef, useState } from "react";
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
          "flex min-h-12 w-full items-center justify-between gap-3 rounded-xl px-3 py-2 text-left transition-colors",
          selected ? "bg-forest-100 ring-1 ring-forest-600/40" : "hover:bg-forest-50",
        )}
      >
        <span className="min-w-0">
          <span className="block truncate text-sm font-medium">{fieldName(field)}</span>
          <span className="block truncate text-xs text-ink-faint">
            {field.county} County · {field.areaHa.toFixed(1)} ha
            {isInDomain(field) ? "" : ` · ${fieldClassLabel[field.fieldClass]}`}
          </span>
        </span>
        {field.role === "primary" ? (
          <span className="shrink-0 rounded-full bg-harvest-100 px-2.5 py-1 font-mono text-[0.6875rem] text-harvest-700">
            Primary
          </span>
        ) : null}
        {selected ? <span className="sr-only">(selected)</span> : null}
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
    <h3 className="flex items-baseline justify-between gap-3 px-3 pt-2 text-xs font-semibold tracking-wide text-ink-faint uppercase">
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

  // Keep the selected row in view inside the list, without moving the page.
  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const box = scrollRef.current;
    const row = box?.querySelector<HTMLElement>('[aria-pressed="true"]');
    if (!box || !row) return;
    const top = row.offsetTop;
    if (
      top < box.scrollTop ||
      top + row.offsetHeight > box.scrollTop + box.clientHeight
    ) {
      box.scrollTop = top - box.clientHeight / 2 + row.offsetHeight / 2;
    }
  }, [selectedId, countyFilter]);

  return (
    <div className="flex max-h-[26rem] min-h-0 flex-1 flex-col gap-2 lg:max-h-none">
      <div
        role="group"
        aria-label="Show fields in"
        className="flex shrink-0 flex-wrap gap-2"
      >
        {countyOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            aria-pressed={countyFilter === option.value}
            onClick={() => onCountyFilterChange(option.value)}
            className={cn(
              "min-h-10 rounded-full border px-4 text-[0.8125rem] font-medium transition-colors sm:text-sm",
              countyFilter === option.value
                ? "border-forest-700 bg-forest-700 text-white"
                : "border-line-strong bg-surface text-ink-soft hover:border-forest-600 hover:bg-forest-50 hover:text-ink",
            )}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div
        ref={scrollRef}
        className="relative min-h-0 flex-1 space-y-1 overflow-y-auto pr-1"
      >
        {primary.length > 0 ? (
          <section aria-label="Primary demo field">
            <GroupHeading>Primary demo field</GroupHeading>
            <ul>
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

        <section aria-label="Test fields">
          <GroupHeading count={rotation.length}>
            Test fields (corn–soybean rotation)
          </GroupHeading>
          <ul>
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

        <section aria-label="Edge-case fields">
          <button
            type="button"
            aria-expanded={edgeOpen}
            aria-disabled={selectedIsEdge}
            onClick={() => setEdgeOpenByUser((open) => !open)}
            className="mt-1 flex min-h-11 w-full items-center justify-between gap-3 rounded-xl px-3 py-2 text-left text-[0.8125rem] font-medium text-ink-soft hover:bg-forest-50"
          >
            <span>
              Edge cases
              <span className="block text-xs font-normal text-ink-faint">
                Not corn–soybean, so we expect “not enough evidence”
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
            <ul>
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
    </div>
  );
}
