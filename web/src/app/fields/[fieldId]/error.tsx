"use client";

import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { routes } from "@/lib/routes";

/**
 * Shown when a field screen cannot load, for example when the comparison service is down. It says what
 * happened and never shows a guessed result in its place.
 */
export default function FieldError({ reset }: { error: Error; reset: () => void }) {
  return (
    <Container className="max-w-3xl py-16 sm:py-24">
      <h1 className="font-display text-4xl font-semibold tracking-tight">
        We could not load this screen
      </h1>
      <p className="mt-4 text-lg text-ink-soft">
        The comparison service did not answer. We have not shown a result, because a guess
        would be worse than none. Try again in a moment.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={reset}
          className="inline-flex min-h-12 items-center justify-center rounded-full bg-forest-700 px-6 text-base font-semibold text-white transition-colors hover:bg-forest-800"
        >
          Try again
        </button>
        <ButtonLink href={routes.field} variant="secondary">
          Choose a field
        </ButtonLink>
      </div>
    </Container>
  );
}
