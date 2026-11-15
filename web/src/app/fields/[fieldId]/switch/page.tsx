import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { connection } from "next/server";
import { Suspense } from "react";
import { Container } from "@/components/ui/container";
import { loadField } from "@/features/field/data/load";
import { TransitionScreen } from "@/features/transition/transition-screen";
import type { Transition } from "@/features/transition/types";
import { readApi } from "@/lib/api-read";

export const metadata: Metadata = { title: "Plan the switch" };

type Props = {
  params: Promise<{ fieldId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default function SwitchPage({ params, searchParams }: Props) {
  return (
    <Container className="max-w-4xl py-10 sm:py-14">
      <Suspense fallback={<p className="text-lg text-ink-soft">Preparing the plan…</p>}>
        <Switch params={params} searchParams={searchParams} />
      </Suspense>
    </Container>
  );
}

async function Switch({ params, searchParams }: Props) {
  const { fieldId } = await params;
  const raw = await searchParams;
  await connection();
  const field = await loadField(fieldId);
  if (!field) notFound();

  // Only B and C have a switch plan; anything else is B, so a hand-edited address still shows something true.
  const strategy = raw.strategy === "C" ? "C" : "B";
  const analysis =
    typeof raw.analysis === "string" && raw.analysis.length <= 64
      ? raw.analysis
      : undefined;
  const query = analysis ? `?analysis_id=${encodeURIComponent(analysis)}` : "";
  const result = await readApi<Transition>(`/strategies/${strategy}/transition${query}`);
  return (
    <TransitionScreen
      fieldId={field.id}
      strategy={strategy}
      analysisId={analysis}
      result={result}
    />
  );
}
