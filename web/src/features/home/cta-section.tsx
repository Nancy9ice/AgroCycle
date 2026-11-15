import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { demoFieldsRoute, routes } from "@/lib/routes";

export function CtaSection() {
  return (
    <section aria-labelledby="cta-title" className="bg-forest-700 py-20 text-white">
      <Container className="flex flex-col items-start justify-between gap-8 md:flex-row md:items-center">
        <div className="max-w-xl">
          <h2
            id="cta-title"
            className="font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl"
          >
            Compare options for your own field, in a few minutes
          </h2>
          <p className="mt-4 text-forest-100">
            Mark your field on the map, answer a few questions, and see what each option
            would ask of your farm. No sign-up. Want to look around first? Try a demo
            field.
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <ButtonLink
            href={routes.field}
            className="bg-white text-forest-800 hover:bg-forest-100 active:bg-forest-200"
          >
            Add your field
          </ButtonLink>
          <ButtonLink
            href={demoFieldsRoute}
            variant="secondary"
            className="border-forest-100/60 bg-transparent text-white hover:border-white hover:bg-forest-800"
          >
            Try a demo field
          </ButtonLink>
        </div>
      </Container>
    </section>
  );
}
