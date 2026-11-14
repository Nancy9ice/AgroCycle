import { cn } from "@/lib/cn";

/** The five steps of the core journey (PRD §5.2). Order matters: it is the user's path. */
export const flowStepLabels = [
  "Field",
  "Profile",
  "Priorities",
  "Compare",
  "Plan",
] as const;

interface FlowStepsProps {
  /** Zero-based index of the current step. */
  current: number;
  className?: string;
}

export function FlowSteps({ current, className }: FlowStepsProps) {
  return (
    <nav aria-label="Progress" className={cn("print:hidden", className)}>
      <p className="font-mono text-xs font-medium tracking-[0.14em] text-forest-600 uppercase sm:hidden">
        Step {current + 1} of {flowStepLabels.length} · {flowStepLabels[current]}
      </p>
      <ol className="hidden items-center gap-2 sm:flex">
        {flowStepLabels.map((label, index) => {
          const state = index < current ? "done" : index === current ? "current" : "todo";
          return (
            <li
              key={label}
              aria-current={state === "current" ? "step" : undefined}
              className="flex items-center gap-2"
            >
              <span
                className={cn(
                  "inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-sm font-medium",
                  state === "current" && "bg-forest-700 text-white",
                  state === "done" && "bg-forest-100 text-forest-800",
                  state === "todo" && "text-ink-faint",
                )}
              >
                <span
                  aria-hidden
                  className={cn(
                    "flex size-5 items-center justify-center rounded-full font-mono text-xs",
                    state === "current" && "bg-white/20",
                    state === "done" && "bg-forest-700 text-white",
                    state === "todo" && "border border-line-strong",
                  )}
                >
                  {index + 1}
                </span>
                {label}
                {state === "done" ? <span className="sr-only"> (completed)</span> : null}
              </span>
              {index < flowStepLabels.length - 1 ? (
                <span aria-hidden className="h-px w-5 bg-line-strong" />
              ) : null}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
