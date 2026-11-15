"use client";

import { ChevronRightIcon } from "@/components/icons/chevron-right-icon";
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
      <ChevronRightIcon className="size-4" />
    </button>
  );
}
