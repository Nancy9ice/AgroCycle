import { Section } from "@/components/ui/section";
import { outcomes, wontClaim } from "@/features/home/content";
import { cn } from "@/lib/cn";

export function HonestySection() {
  return (
    <Section
      id="honesty"
      eyebrow="Honest by design"
      title="An answer you can trust, even when it is “we're not sure”"
      intro="AgroCycle can say “worth a closer look”, “no clear winner” or “not enough evidence”. It never has to pick a winner, and it never treats missing data as good news."
      tone="dark"
    >
      <ul className="grid gap-5 md:grid-cols-3">
        {outcomes.map((outcome) => (
          <li
            key={outcome.title}
            className="rounded-[var(--radius-card)] bg-forest-800/70 p-7 ring-1 ring-white/10"
          >
            <span
              className={cn(
                "inline-block rounded-full px-3.5 py-1.5 text-sm font-semibold",
                outcome.tone,
              )}
            >
              {outcome.title}
            </span>
            <p className="mt-5 text-forest-100">{outcome.body}</p>
          </li>
        ))}
      </ul>

      <div className="mt-12 rounded-[var(--radius-card)] border border-white/15 p-7 sm:p-9">
        <h3 className="font-display text-xl font-semibold">What AgroCycle will not do</h3>
        <ul className="mt-5 grid gap-x-10 gap-y-3 sm:grid-cols-2">
          {wontClaim.map((item) => (
            <li key={item} className="flex items-start gap-3 text-forest-100">
              <svg
                viewBox="0 0 20 20"
                className="mt-1 size-4 shrink-0 text-harvest-500"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                aria-hidden
              >
                <path d="M5 5l10 10M15 5L5 15" />
              </svg>
              {item}
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}
