import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { FlowSteps } from "@/components/layout/flow-steps";
import { Container } from "@/components/ui/container";
import { demoFields, getFieldById } from "@/features/field/data";
import { EdgeCaseNote } from "@/features/field/edge-case-note";
import { fieldName, isInDomain } from "@/features/field/labels";
import { PrioritiesForm } from "@/features/priorities/priorities-form";

export const metadata: Metadata = {
  title: "What matters to you",
  description:
    "Say what matters and what is possible on your farm: manure, equipment, buyers, storage and labour. Every question is optional.",
};

export function generateStaticParams() {
  return demoFields.map((field) => ({ fieldId: field.id }));
}

export default function PrioritiesPage({
  params,
}: {
  params: Promise<{ fieldId: string }>;
}) {
  return (
    <Container className="max-w-6xl py-10 sm:py-14">
      <FlowSteps current={2} />
      {/* Route params are read inside Suspense so navigation can show the shell instantly. */}
      <Suspense
        fallback={
          <div
            aria-busy
            className="mt-8 h-96 animate-pulse rounded-[var(--radius-card)] bg-sunken"
          />
        }
      >
        <Priorities params={params} />
      </Suspense>
    </Container>
  );
}

async function Priorities({
  params,
}: {
  params: Promise<{ fieldId: string }>;
}) {
  const { fieldId } = await params;
  const field = getFieldById(fieldId);
  if (!field) notFound();

  return (
    <>
      <header className="mt-8 max-w-3xl">
        <h1 className="font-display text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
          What matters, and what is possible?
        </h1>
        <p className="mt-4 text-lg text-ink-soft">
          For {fieldName(field)}. Every question is optional. If you skip one, we treat it
          as “don&rsquo;t know”, not “yes”. Priorities change what we highlight first.
          Practical answers decide which comparisons fit your farm. Nothing is hidden, and
          there is no single score.
        </p>
      </header>

      <div className="mt-8 space-y-8">
        {!isInDomain(field) ? <EdgeCaseNote /> : null}
        {/* The form reads the URL, which needs a Suspense boundary. */}
        <Suspense
          fallback={
            <div
              aria-busy
              className="h-96 animate-pulse rounded-[var(--radius-card)] bg-sunken"
            />
          }
        >
          <PrioritiesForm fieldId={field.id} />
        </Suspense>
      </div>
    </>
  );
}
