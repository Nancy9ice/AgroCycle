import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Container } from "@/components/ui/container";
import { getComparison } from "@/features/compare/get-comparison";
import { demoFields } from "@/features/field/data";
import { parseAnswers } from "@/features/priorities/answers-codec";
import { PlanScreen } from "@/features/plan/plan-screen";

export const metadata: Metadata = { title: "Brief for an adviser" };

export function generateStaticParams() {
  return demoFields.map((field) => ({ fieldId: field.id }));
}

type FieldPageProps = {
  params: Promise<{ fieldId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default function PlanPage({ params, searchParams }: FieldPageProps) {
  return (
    <Container className="max-w-[90rem] py-6 sm:py-8">
      <Suspense
        fallback={<p className="text-lg text-ink-soft">Preparing the summary…</p>}
      >
        <Plan params={params} searchParams={searchParams} />
      </Suspense>
    </Container>
  );
}

async function Plan({ params, searchParams }: FieldPageProps) {
  const { fieldId } = await params;
  const raw = await searchParams;
  const query = new URLSearchParams(
    Object.entries(raw).flatMap(([key, value]) =>
      typeof value === "string" ? ([[key, value]] as [string, string][]) : [],
    ),
  );
  const answers = parseAnswers(query);
  const comparison = await getComparison(fieldId, answers, {
    preview: query.get("preview") === "sample",
  });
  if (!comparison) notFound();
  return <PlanScreen comparison={comparison} answers={answers} />;
}
