import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { connection } from "next/server";
import { Suspense } from "react";
import { Container } from "@/components/ui/container";
import { IndicatorScreen } from "@/features/evidence/indicator-screen";
import type { Lineage } from "@/features/evidence/methods-types";
import { readApi } from "@/lib/api-read";

export const metadata: Metadata = { title: "Indicator method" };

export default function IndicatorPage({
  params,
}: {
  params: Promise<{ indicatorId: string }>;
}) {
  return (
    <Container className="max-w-4xl py-10 sm:py-14">
      <Suspense
        fallback={
          <div
            aria-busy
            className="h-96 animate-pulse rounded-[var(--radius-card)] bg-sunken"
          />
        }
      >
        <Indicator params={params} />
      </Suspense>
    </Container>
  );
}

async function Indicator({ params }: { params: Promise<{ indicatorId: string }> }) {
  const { indicatorId } = await params;
  await connection();
  const result = await readApi<Lineage>(`/lineage/${encodeURIComponent(indicatorId)}`);
  if (result.status === "not_found") notFound();
  return <IndicatorScreen result={result} />;
}
