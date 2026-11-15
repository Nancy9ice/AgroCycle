import type { Metadata } from "next";
import { connection } from "next/server";
import { Suspense } from "react";
import { Container } from "@/components/ui/container";
import { loadFieldData } from "@/features/field/data/load";
import { FieldEntry } from "@/features/field/field-entry";

export const metadata: Metadata = {
  title: "Add your field",
  description:
    "Mark your field on a satellite map, or try a demo field, in Story or Boone County, Iowa.",
};

export default function FieldPage() {
  return (
    <Container className="max-w-[90rem] py-6 sm:py-8">
      <Suspense
        fallback={
          <div
            aria-busy
            className="h-[30rem] animate-pulse rounded-[var(--radius-card)] bg-sunken"
          />
        }
      >
        <FieldStep />
      </Suspense>
    </Container>
  );
}

async function FieldStep() {
  // Per request: the fields and county outlines come from the API, which changes when the data pipeline runs.
  await connection();
  const { fields, counties } = await loadFieldData();
  return <FieldEntry fields={fields} counties={counties} />;
}
