import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { connection } from "next/server";
import { Suspense } from "react";
import { Container } from "@/components/ui/container";
import { CompareScreen } from "@/features/compare/compare-screen";
import { getSavedComparison } from "@/features/compare/get-saved-comparison";

export const metadata: Metadata = { title: "Saved comparison" };

export default function SavedComparisonPage({
  params,
}: {
  params: Promise<{ analysisId: string }>;
}) {
  return (
    <Container className="max-w-6xl py-10 sm:py-14">
      <Suspense
        fallback={<p className="text-lg text-ink-soft">Opening the saved comparison…</p>}
      >
        <Saved params={params} />
      </Suspense>
    </Container>
  );
}

async function Saved({ params }: { params: Promise<{ analysisId: string }> }) {
  const { analysisId } = await params;
  // The stored result comes from the API, per request.
  await connection();
  const comparison = await getSavedComparison(analysisId);
  if (!comparison) notFound();
  // A stored result has no priorities answers to hand back: it keeps the decision, not the form.
  return <CompareScreen comparison={comparison} answers={{}} />;
}
