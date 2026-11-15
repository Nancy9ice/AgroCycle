import type { Metadata } from "next";
import { connection } from "next/server";
import { Suspense } from "react";
import { Container } from "@/components/ui/container";
import { getTestSet } from "@/features/validation/get-test-set";
import { ValidationScreen } from "@/features/validation/validation-screen";

export const metadata: Metadata = {
  title: "How we checked this",
  description:
    "What has been checked in AgroCycle, by which kind of check, and what has not.",
};

export default function ValidationPage() {
  return (
    <Container className="max-w-5xl py-6 sm:py-8">
      <Suspense
        fallback={
          <div
            aria-busy
            className="h-96 animate-pulse rounded-[var(--radius-card)] bg-sunken"
          />
        }
      >
        <Validation />
      </Suspense>
    </Container>
  );
}

async function Validation() {
  // The test-field results come from the data service and change when the engine is re-run.
  await connection();
  return <ValidationScreen testSet={await getTestSet()} />;
}
