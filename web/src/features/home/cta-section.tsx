import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { routes } from "@/lib/routes";

export function CtaSection() {
  return (
    <section aria-labelledby="cta-title" className="bg-forest-700 py-20 text-white">
      <Container className="flex flex-col items-start justify-between gap-8 md:flex-row md:items-center">
        <div className="max-w-xl">
          <h2
            id="cta-title"
            className="font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl"
          >
            See it on a real example, in a few minutes
          </h2>
          <p className="mt-4 text-forest-100">
            The demo field is a demonstration polygon in Story County. No sign-up, and
            every result has a link you can share.
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <ButtonLink
            href={routes.field}
            className="bg-white text-forest-800 hover:bg-forest-100 active:bg-forest-200"
          >
            Start with the demo field
          </ButtonLink>
        </div>
      </Container>
    </section>
  );
}
