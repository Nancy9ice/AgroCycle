import { Section } from "@/components/ui/section";
import { flowSteps } from "@/features/home/content";

export function HowItWorksSection() {
  return (
    <Section
      id="how-it-works"
      eyebrow="How it works"
      title="Five steps from your field to a plan you can discuss"
      tone="sunken"
    >
      <ol className="grid gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-5">
        {flowSteps.map((step, index) => (
          <li key={step.title} className="relative">
            <div className="flex items-center gap-3">
              <span className="font-display text-5xl leading-none font-semibold text-forest-600/30">
                {index + 1}
              </span>
              {index < flowSteps.length - 1 ? (
                <span
                  aria-hidden
                  className="hidden h-px flex-1 bg-line-strong lg:block"
                />
              ) : null}
            </div>
            <h3 className="mt-3 text-lg font-semibold">{step.title}</h3>
            <p className="mt-2 text-[0.9375rem] text-ink-soft">{step.body}</p>
          </li>
        ))}
      </ol>
    </Section>
  );
}
