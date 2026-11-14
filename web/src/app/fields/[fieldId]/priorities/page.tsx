import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { FlowSteps } from "@/components/layout/flow-steps";
import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { demoFields, getFieldById } from "@/features/field/data";
import { fieldName } from "@/features/field/labels";
import { profileRoute } from "@/lib/routes";

export const metadata: Metadata = { title: "What matters to you" };

export function generateStaticParams() {
  return demoFields.map((field) => ({ fieldId: field.id }));
}

/** Placeholder until the priorities task (Phase 11, FE) replaces it. */
export default function PrioritiesPage({
  params,
}: PageProps<"/fields/[fieldId]/priorities">) {
  return (
    <Container className="max-w-6xl py-10 sm:py-14">
      <FlowSteps current={2} />
      <h1 className="mt-8 font-display text-4xl font-semibold tracking-tight sm:text-5xl">
        What matters to you
      </h1>
      <Suspense fallback={<p className="mt-4 text-lg text-ink-soft">Loading field…</p>}>
        <Selected params={params} />
      </Suspense>
    </Container>
  );
}

async function Selected({
  params,
}: {
  params: PageProps<"/fields/[fieldId]/priorities">["params"];
}) {
  const { fieldId } = await params;
  const field = getFieldById(fieldId);
  if (!field) notFound();
  return (
    <>
      <p className="mt-4 max-w-xl text-lg text-ink-soft">
        {fieldName(field)} is selected. The priorities and constraints form is the next
        screen to be built.
      </p>
      <ButtonLink href={profileRoute(field.id)} variant="secondary" className="mt-8">
        Back to the field profile
      </ButtonLink>
    </>
  );
}
