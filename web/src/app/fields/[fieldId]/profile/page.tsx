import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { FlowSteps } from "@/components/layout/flow-steps";
import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { demoFields, getFieldById } from "@/features/field/data";
import { fieldName } from "@/features/field/labels";
import { fieldRoute } from "@/lib/routes";

export const metadata: Metadata = { title: "Your field" };

export function generateStaticParams() {
  return demoFields.map((field) => ({ fieldId: field.id }));
}

/** Placeholder until the profile task (Phase 7, FE) replaces it. */
export default function ProfilePage({ params }: PageProps<"/fields/[fieldId]/profile">) {
  return (
    <Container className="max-w-7xl py-10 sm:py-14">
      <FlowSteps current={1} />
      <h1 className="mt-8 font-display text-4xl font-semibold tracking-tight sm:text-5xl">
        Your field
      </h1>
      {/* Route params are read inside Suspense so navigation can show the shell instantly. */}
      <Suspense fallback={<p className="mt-4 text-lg text-ink-soft">Loading field…</p>}>
        <SelectedField params={params} />
      </Suspense>
    </Container>
  );
}

async function SelectedField({
  params,
}: {
  params: PageProps<"/fields/[fieldId]/profile">["params"];
}) {
  const { fieldId } = await params;
  const field = getFieldById(fieldId);
  if (!field) notFound();

  return (
    <>
      <p className="mt-4 max-w-xl text-lg text-ink-soft">
        {fieldName(field)} is selected. The field profile is the next screen to be built.
      </p>
      <ButtonLink href={fieldRoute(field.id)} variant="secondary" className="mt-8">
        Back to choosing a field
      </ButtonLink>
    </>
  );
}
