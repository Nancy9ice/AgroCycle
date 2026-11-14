import type { Metadata } from "next";
import { Suspense } from "react";
import { FlowSteps } from "@/components/layout/flow-steps";
import { Container } from "@/components/ui/container";
import { FieldSelection } from "@/features/field/field-selection";

export const metadata: Metadata = {
  title: "Choose your field",
  description:
    "Pick the demo field or a test field in Story or Boone County, Iowa, and check its boundary before building a field profile.",
};

export default function FieldPage() {
  return (
    <Container className="max-w-7xl py-10 sm:py-14">
      <FlowSteps current={0} />
      <header className="mt-8 max-w-3xl">
        <h1 className="font-display text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
          Choose a field
        </h1>
        <p className="mt-4 text-lg text-ink-soft">
          Start with the demo field or pick a test field. Every field here is a
          demonstration polygon inside Story or Boone County, Iowa, not a real farm.
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
          <FieldSelection />
        </Suspense>
      </div>
    </Container>
  );
}
