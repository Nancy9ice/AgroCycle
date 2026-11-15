import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Container } from "@/components/ui/container";
import { CompareScreen } from "@/features/compare/compare-screen";
import { getComparison } from "@/features/compare/get-comparison";
import { parseAnswers } from "@/features/priorities/answers-codec";

export const metadata: Metadata = { title: "Compare the options" };

type FieldPageProps = {
  params: Promise<{ fieldId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default function ComparePage({ params, searchParams }: FieldPageProps) {
  return (
    <Container className="max-w-[90rem] py-6 sm:py-8">
      <Suspense
        fallback={<p className="text-lg text-ink-soft">Comparing the options…</p>}
      >
        <Comparison params={params} searchParams={searchParams} />
      </Suspense>
    </Container>
  );
}

async function Comparison({ params, searchParams }: FieldPageProps) {
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

  return <CompareScreen comparison={comparison} answers={answers} />;
}
