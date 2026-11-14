import { cropPhases, type Strategy } from "@/domain/strategies";
import { cn } from "@/lib/cn";

interface RotationRibbonProps {
  strategy: Strategy;
  className?: string;
}

/**
 * Shows one rotation as a segmented bar plus a year-by-year list.
 * Colour is always paired with a text label so meaning never depends on colour alone.
 */
export function RotationRibbon({ strategy, className }: RotationRibbonProps) {
  const years = strategy.phases.length;

  return (
    <div className={className}>
      <div aria-hidden className="flex h-3 gap-1 overflow-hidden rounded-full">
        {strategy.phases.map((id, index) => (
          <span
            key={`${id}-${index}`}
            className={cn("h-full flex-1", cropPhases[id].swatch)}
          />
        ))}
      </div>

      <ol className="mt-5 space-y-2.5">
        {strategy.phases.map((id, index) => (
          <li key={`${id}-${index}`} className="flex items-center gap-3 text-[0.9375rem]">
            <span className="w-14 shrink-0 font-mono text-xs text-ink-faint">
              Year {index + 1}
            </span>
            <span
              aria-hidden
              className={cn("size-3 shrink-0 rounded-full", cropPhases[id].swatch)}
            />
            <span className="font-medium">{cropPhases[id].label}</span>
          </li>
        ))}
      </ol>

      <p className="mt-4 font-mono text-xs text-ink-faint">Repeats every {years} years</p>
    </div>
  );
}
