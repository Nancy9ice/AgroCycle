import { RotationRibbon } from "@/components/rotation/rotation-ribbon";
import { Section } from "@/components/ui/section";
import { strategies } from "@/domain/strategies";
import { cn } from "@/lib/cn";

export function StrategiesSection() {
  return (
    <Section
      id="strategies"
      eyebrow="Three options, side by side"
      title="Your rotation, and two longer ones"
      intro="Each option is a comparison scenario drawn from a real Iowa field trial. None of them is a recommendation."
    >
      <ul className="grid gap-6 md:grid-cols-3">
        {strategies.map((strategy) => {
          const isExisting = strategy.id === "A";
          return (
            <li
              key={strategy.id}
              className={cn(
                "flex flex-col rounded-[var(--radius-card)] border bg-surface p-7 shadow-card",
                isExisting ? "border-line" : "border-forest-200",
              )}
            >
              <div className="flex items-center justify-between">
                <span className="flex size-11 items-center justify-center rounded-full bg-forest-700 font-display text-xl font-semibold text-white">
                  {strategy.id}
                </span>
                <span
                  className={cn(
                    "rounded-full px-3 py-1 font-mono text-xs font-medium",
                    isExisting
                      ? "bg-sunken text-ink-soft"
                      : "bg-forest-100 text-forest-800",
                  )}
                >
                  {strategy.kind}
                </span>
              </div>

              <h3 className="mt-5 font-display text-2xl font-semibold">
                {strategy.name}
              </h3>
              <p className="mt-2 text-ink-soft">{strategy.summary}</p>

              <RotationRibbon
                strategy={strategy}
                className="mt-7 border-t border-line pt-7"
              />
            </li>
          );
        })}
      </ul>

      <p className="mt-8 max-w-3xl text-sm text-ink-faint">
        Anchored to the rotations in the Marsden Farm experiment (Davis et al., 2012, PLOS
        ONE). Results from one research farm are not predictions for your field, and
        AgroCycle checks how well they apply to yours before using them.
      </p>
    </Section>
  );
}
