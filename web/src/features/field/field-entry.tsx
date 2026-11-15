"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AddYourField } from "./add-your-field";
import { FieldSelection } from "./field-selection";
import { cn } from "@/lib/cn";
import type { County, DemoField } from "./types";

type Mode = "own" | "demo";

const tabs: readonly { mode: Mode; label: string }[] = [
  { mode: "own", label: "My field" },
  { mode: "demo", label: "Try a demo field" },
];

/**
 * Step 1 has two ways in. A farmer's own field comes first; the demo fields are for seeing how the
 * product works. The choice lives in the URL (`?mode=demo`), and a link with `?field=` opens the demo
 * tab so returning from a profile still lands where it left.
 */
export function FieldEntry({
  fields,
  counties,
}: {
  fields: readonly DemoField[];
  counties: readonly County[];
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const mode: Mode =
    searchParams.get("mode") === "demo" || searchParams.has("field") ? "demo" : "own";

  const choose = (next: Mode) => {
    if (next === mode) return;
    const params = new URLSearchParams(searchParams.toString());
    params.delete("field");
    params.set("mode", next);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

  return (
    <div className="space-y-8">
      <div
        role="group"
        aria-label="How do you want to start?"
        className="inline-flex w-full max-w-md rounded-full border border-line-strong bg-surface p-1 sm:w-auto"
      >
        {tabs.map((tab) => (
          <button
            key={tab.mode}
            type="button"
            aria-pressed={mode === tab.mode}
            onClick={() => choose(tab.mode)}
            className={cn(
              "min-h-11 flex-1 rounded-full px-5 text-[0.9375rem] font-semibold transition-colors sm:flex-none",
              mode === tab.mode
                ? "bg-forest-700 text-white"
                : "text-ink hover:bg-forest-50",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {mode === "own" ? (
        <AddYourField counties={counties} />
      ) : (
        <FieldSelection fields={fields} counties={counties} />
      )}
    </div>
  );
}
