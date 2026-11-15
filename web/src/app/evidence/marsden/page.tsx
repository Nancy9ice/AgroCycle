import type { Metadata } from "next";
import { connection } from "next/server";
import { Suspense } from "react";
import { Container } from "@/components/ui/container";
import { MarsdenScreen } from "@/features/evidence/marsden-screen";
import type { Marsden } from "@/features/evidence/marsden-table";
import { readApi } from "@/lib/api-read";

export const metadata: Metadata = {
  title: "Marsden Farm evidence",
  description:
    "The long-running Iowa experiment the comparison rests on: the reproduced figures and what they do not show.",
};

export default function MarsdenPage() {
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
        <MarsdenData />
      </Suspense>
    </Container>
  );
}

async function MarsdenData() {
  await connection();
  return <MarsdenScreen result={await readApi<Marsden>("/evidence/marsden")} />;
}
