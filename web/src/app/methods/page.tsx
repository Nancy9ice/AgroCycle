import type { Metadata } from "next";
import { connection } from "next/server";
import { Suspense } from "react";
import { Container } from "@/components/ui/container";
import { MethodsScreen } from "@/features/evidence/methods-screen";
import type { Health, IndicatorSummary, Source } from "@/features/evidence/methods-types";
import { readApi } from "@/lib/api-read";

export const metadata: Metadata = {
  title: "Data and methods",
  description:
    "Where every number in AgroCycle comes from: the data sources, the indicators, and the limits of each.",
};

export default function MethodsPage() {
  return (
    <Container className="max-w-5xl py-10 sm:py-14">
      <Suspense
        fallback={
          <div
            aria-busy
            className="h-96 animate-pulse rounded-[var(--radius-card)] bg-sunken"
          />
        }
      >
        <Methods />
      </Suspense>
    </Container>
  );
}

async function Methods() {
  await connection();
  const [sources, indicators, health] = await Promise.all([
    readApi<Source[]>("/sources"),
    readApi<IndicatorSummary[]>("/indicators"),
    readApi<Health>("/health"),
  ]);
  return <MethodsScreen sources={sources} indicators={indicators} health={health} />;
}
