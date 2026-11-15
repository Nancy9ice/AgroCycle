import type { Metadata } from "next";
import { Suspense } from "react";
import { FlowSteps } from "@/components/layout/flow-steps";
import { Container } from "@/components/ui/container";
import { FieldEntry } from "@/features/field/field-entry";

export const metadata: Metadata = {
  title: "Add your field",
  description:
    "Mark your field on a satellite map, or try a demo field, in Story or Boone County, Iowa.",
};

export default function FieldPage() {
  return (
    <Container className="max-w-9xl py-10 sm:py-14">
      <FlowSteps current={0} />
      <header className="mt-8 max-w-3xl">
        <h1 className="font-display text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
          Add your field
        </h1>
        <p className="mt-4 text-lg text-ink-soft">
          Mark your field on the map, or find it with your phone’s location. We cover
          Story and Boone counties, Iowa for now. Want to see how it works first? Try a
          demo field. Those are practice fields, not real farms.
        </p>
      </header>

      <div className="mt-10">
        <Suspense
          fallback={
            <div
              aria-busy
              className="h-[30rem] animate-pulse rounded-[var(--radius-card)] bg-sunken"
            />
          }
        >
          <FieldEntry />
        </Suspense>
      </div>
    </Container>
  );
}
