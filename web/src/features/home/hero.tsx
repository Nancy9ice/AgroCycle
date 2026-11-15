import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { HeroFieldVisual } from "@/features/home/hero-field-visual";
import { demoFieldsRoute, routes } from "@/lib/routes";
import { site } from "@/lib/site";

const assurances = [
  "No account needed",
  "Every number shows its source",
  "Iowa pilot: Story and Boone counties",
] as const;

export function Hero() {
  return (
    <section
      aria-labelledby="hero-title"
      className="relative overflow-hidden bg-[radial-gradient(60rem_30rem_at_85%_-10%,var(--color-forest-100),transparent)] pt-12 pb-20 sm:pt-20 sm:pb-28"
    >
      <Container className="grid items-center gap-14 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16">
        <div>
          <p className="inline-flex items-center gap-2 rounded-full border border-forest-200 bg-forest-50 px-3.5 py-1.5 font-mono text-xs font-medium tracking-wide text-forest-700">
            <span aria-hidden className="size-1.5 rounded-full bg-forest-600" />
            NASA Space Apps 2026 · Field Shift
          </p>

          <h1
            id="hero-title"
            className="mt-6 font-display text-[2.5rem] leading-[1.05] font-semibold tracking-tight text-balance sm:text-6xl"
          >
            Should this field stay in corn and soybeans?
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-relaxed text-pretty text-ink-soft sm:text-xl">
            {site.description}
          </p>

          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <ButtonLink href={routes.field}>Add your field</ButtonLink>
            <ButtonLink href={demoFieldsRoute} variant="secondary">
              Try a demo field first
            </ButtonLink>
          </div>

          <ul className="mt-9 flex flex-col gap-2.5 text-[0.9375rem] text-ink-soft sm:flex-row sm:flex-wrap sm:gap-x-6">
            {assurances.map((text) => (
              <li key={text} className="inline-flex items-center gap-2">
                <svg
                  viewBox="0 0 20 20"
                  className="size-4 shrink-0 text-forest-600"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden
                >
                  <path d="M4 10.5l4 4 8-9" />
                </svg>
                {text}
              </li>
            ))}
          </ul>
        </div>

        <HeroFieldVisual />
      </Container>
    </section>
  );
}
