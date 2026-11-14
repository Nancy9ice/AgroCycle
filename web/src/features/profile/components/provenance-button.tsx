"use client";

import { cn } from "@/lib/cn";
import type { Provenance } from "../types";
import { useProfileUi } from "./profile-ui";

interface ProvenanceButtonProps {
  provenance: Provenance;
  isSample?: boolean;
  className?: string;
}

/** Opens the shared drawer that explains where a number comes from (FR-12). */
export function ProvenanceButton({
  provenance,
  isSample = false,
  className,
}: ProvenanceButtonProps) {
  const { openProvenance } = useProfileUi();
  return (
    <button
      type="button"
      onClick={() => openProvenance(provenance, isSample)}
      className={cn(
        "inline-flex min-h-11 items-center gap-1.5 rounded-full px-3 text-sm font-semibold text-forest-700 hover:bg-forest-100",
        className,
      )}
    >
      Where this comes from
      <span className="sr-only">: {provenance.title}</span>
      <svg
        viewBox="0 0 20 20"
        className="size-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden
      >
        <path d="M8 5l5 5-5 5" />
      </svg>
    </button>
  );
}
