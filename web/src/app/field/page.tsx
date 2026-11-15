import type { Metadata } from "next";
import { Suspense } from "react";
import { Container } from "@/components/ui/container";
import { FieldEntry } from "@/features/field/field-entry";

export const metadata: Metadata = {
  title: "Add your field",
  description:
    "Mark your field on a satellite map, or try a demo field, in Story or Boone County, Iowa.",
};

export default function FieldPage() {
  return (
    <Container className="max-w-9xl py-6 sm:py-8">
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
    </Container>
  );
}
