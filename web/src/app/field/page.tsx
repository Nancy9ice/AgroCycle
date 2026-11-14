import type { Metadata } from "next";
import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { routes } from "@/lib/routes";

export const metadata: Metadata = { title: "Choose your field" };

/** Placeholder until the field-selection task (Phase 7, FE) replaces it. */
export default function FieldPage() {
  return (
    <Container className="py-24">
      <p className="font-mono text-xs font-medium tracking-[0.14em] text-forest-600 uppercase">
        Step 1 of 5
      </p>
      <h1 className="mt-3 font-display text-4xl font-semibold tracking-tight">
        Choose your field
      </h1>
      <p className="mt-4 max-w-xl text-lg text-ink-soft">
        Field selection is the next screen to be built.
      </p>
      <ButtonLink href={routes.home} variant="secondary" className="mt-8">
        Back to home
      </ButtonLink>
    </Container>
  );
}
