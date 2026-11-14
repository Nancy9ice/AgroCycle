"use client";

import { cn } from "@/lib/cn";
import { useProfileUi, type ProfileView } from "./profile-ui";

const options: readonly { value: ProfileView; label: string }[] = [
  { value: "simple", label: "Simple" },
  { value: "detailed", label: "Detailed" },
];

/** Detailed adds the technical lines to each card. The evidence label is always shown. */
export function ViewToggle() {
  const { view, setView } = useProfileUi();
  return (
    <div
      role="group"
      aria-label="Level of detail"
      className="inline-flex gap-1 rounded-full bg-sunken p-1"
    >
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={view === option.value}
          onClick={() => setView(option.value)}
          className={cn(
            "min-h-10 rounded-full px-4 text-sm font-semibold transition-colors",
            view === option.value
              ? "bg-surface text-forest-800 shadow-sm"
              : "text-ink-soft hover:text-ink",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
