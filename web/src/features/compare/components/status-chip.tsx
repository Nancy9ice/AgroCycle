import { cn } from "@/lib/cn";

export type Tone = "good" | "caution" | "stop" | "neutral";

const tones: Record<Tone, string> = {
  good: "border-forest-200 bg-forest-100 text-forest-800",
  caution: "border-harvest-500/50 bg-harvest-100 text-harvest-700",
  stop: "border-clay-700/30 bg-clay-100 text-clay-700",
  neutral: "border-line-strong bg-sunken text-ink-soft",
};

interface StatusChipProps {
  tone: Tone;
  glyph: string;
  children: string;
  className?: string;
}

/** A state in words plus a glyph, so meaning never depends on colour alone. */
export function StatusChip({ tone, glyph, children, className }: StatusChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-semibold",
        tones[tone],
        className,
      )}
    >
      <span aria-hidden className="font-mono text-xs leading-none">
        {glyph}
      </span>
      {children}
    </span>
  );
}
