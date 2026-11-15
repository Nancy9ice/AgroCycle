"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { PageHeader } from "@/components/layout/page-header";
import { cn } from "@/lib/cn";
import { routes } from "@/lib/routes";
import { AddYourField } from "./add-your-field";
import { FieldSelection } from "./field-selection";
import type { County, DemoField } from "./types";

type Mode = "own" | "demo";

const tabs: readonly { mode: Mode; label: string }[] = [
  { mode: "own", label: "My field" },
  { mode: "demo", label: "Try a demo field" },
];

const intro: Record<Mode, string> = {
  own: "Tap the corners of your field on the satellite map. Story and Boone counties, Iowa.",
  demo: "Practice fields, not real farms. Pick one to see how AgroCycle works.",
};

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
    <div className="space-y-6">
      <PageHeader
        title="Add your field"
        back={{ href: routes.home, label: "home" }}
        aside={
          <div
            role="group"
            aria-label="How do you want to start?"
            className="inline-flex rounded-full border border-line-strong bg-surface p-1"
          >
            {tabs.map((tab) => (
              <button
                key={tab.mode}
                type="button"
                aria-pressed={mode === tab.mode}
                onClick={() => choose(tab.mode)}
                className={cn(
                  "min-h-10 rounded-full px-3.5 text-[0.8125rem] font-medium transition-colors sm:px-5 sm:text-sm",
                  mode === tab.mode
                    ? "bg-forest-700 text-white"
                    : "text-ink hover:bg-forest-50",
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>
        }
      >
        <p className="hidden sm:block">{intro[mode]}</p>
      </PageHeader>

      {mode === "own" ? (
        <AddYourField counties={counties} />
      ) : (
        <FieldSelection fields={fields} counties={counties} />
      )}
    </div>
  );
}
