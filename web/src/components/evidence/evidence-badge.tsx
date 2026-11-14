import { evidenceTypes, type EvidenceTypeId } from "@/domain/evidence";
import { cn } from "@/lib/cn";

interface EvidenceBadgeProps {
  type: EvidenceTypeId;
  className?: string;
}

/**
 * Labels what kind of evidence a value is (PRD §6.2). Reused on every screen that shows
 * a material output, so the vocabulary stays identical across the product.
 */
export function EvidenceBadge({ type, className }: EvidenceBadgeProps) {
  const { label, meaning } = evidenceTypes[type];
  return (
    <span
      title={meaning}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-line-strong bg-surface px-2.5 py-1 font-mono text-xs font-medium text-ink-soft",
        className,
      )}
    >
      <span aria-hidden className="size-1.5 rounded-full bg-forest-600" />
      {label}
    </span>
  );
}
