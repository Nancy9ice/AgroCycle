import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { FlowSteps } from "@/components/layout/flow-steps";
import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { demoFields, getFieldById } from "@/features/field/data";
import { fieldName } from "@/features/field/labels";
import { parseAnswers, serializeAnswers } from "@/features/priorities/answers-codec";
import { optionLabel, questions } from "@/features/priorities/questions";
import { prioritiesRoute } from "@/lib/routes";

export const metadata: Metadata = { title: "Compare the options" };

export function generateStaticParams() {
  return demoFields.map((field) => ({ fieldId: field.id }));
}

/** Placeholder until the comparison task (Phase 11, FE) replaces it. Echoes the answers it received. */
export default function ComparePage({
  params,
  searchParams,
}: PageProps<"/fields/[fieldId]/compare">) {
  return (
    <Container className="max-w-6xl py-10 sm:py-14">
      <FlowSteps current={3} />
      <h1 className="mt-8 font-display text-4xl font-semibold tracking-tight sm:text-5xl">
        Compare the options
      </h1>
      <Suspense fallback={<p className="mt-4 text-lg text-ink-soft">Loading…</p>}>
        <Received params={params} searchParams={searchParams} />
      </Suspense>
    </Container>
  );
}

async function Received({
  params,
  searchParams,
}: Pick<PageProps<"/fields/[fieldId]/compare">, "params" | "searchParams">) {
  const { fieldId } = await params;
  const field = getFieldById(fieldId);
  if (!field) notFound();

  const raw = await searchParams;
  const query = new URLSearchParams(
    Object.entries(raw).flatMap(([key, value]) =>
      typeof value === "string" ? ([[key, value]] as [string, string][]) : [],
    ),
  );
  const answers = parseAnswers(query);

  return (
    <>
      <p className="mt-4 max-w-xl text-lg text-ink-soft">
        {fieldName(field)} is selected. The comparison is the next screen to be built.
        This is what it will receive from your answers:
      </p>
      <dl className="mt-6 max-w-2xl divide-y divide-line rounded-2xl border border-line bg-surface">
        {questions.map((question) => {
          const label = optionLabel(question, answers[question.id]);
          return (
            <div
              key={question.id}
              className="grid gap-1 px-5 py-3 sm:grid-cols-[1fr_10rem] sm:gap-4"
            >
              <dt className="text-[0.9375rem]">{question.label}</dt>
              <dd className={label ? "font-semibold" : "text-ink-faint"}>
                {label ?? "Not provided"}
              </dd>
            </div>
          );
        })}
      </dl>
      <ButtonLink
        href={prioritiesRoute(field.id, serializeAnswers(answers))}
        variant="secondary"
        className="mt-8"
      >
        Change my answers
      </ButtonLink>
    </>
  );
}
