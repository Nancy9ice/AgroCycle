import { Section } from "@/components/ui/section";
import { decisionPoints } from "@/features/home/content";

export function DecisionSection() {
  return (
    <Section
      id="decision"
      eyebrow="The decision we support"
      title="One question, answered with evidence and its limits"
      tone="sunken"
    >
      <div className="grid gap-12 lg:grid-cols-[1fr_1fr] lg:gap-16">
        <blockquote className="border-l-4 border-forest-600 pl-6 font-display text-2xl leading-snug text-pretty sm:text-[1.75rem]">
          Given a field under a corn–soybean rotation in Story or Boone County, Iowa, what
          does the evidence say about keeping it, versus two longer rotations?
        </blockquote>

        <ol className="space-y-7">
          {decisionPoints.map((point, index) => (
            <li key={point.title} className="flex gap-4">
              <span
                aria-hidden
                className="flex size-9 shrink-0 items-center justify-center rounded-full bg-forest-700 font-mono text-sm font-semibold text-white"
              >
                {index + 1}
              </span>
              <div>
                <h3 className="text-lg font-semibold">{point.title}</h3>
                <p className="mt-1 text-ink-soft">{point.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </Section>
  );
}
