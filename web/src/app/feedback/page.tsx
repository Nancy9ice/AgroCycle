import type { Metadata } from "next";
import { Suspense } from "react";
import { Container } from "@/components/ui/container";
import { PageHeader } from "@/components/layout/page-header";
import { FeedbackForm } from "@/features/feedback/feedback-form";
import { routes } from "@/lib/routes";

export const metadata: Metadata = {
  title: "Give feedback",
  description: "Tell us how useful and how clear AgroCycle was, and what was missing.",
};

type Search = Promise<Record<string, string | string[] | undefined>>;

const one = (value: string | string[] | undefined) =>
  typeof value === "string" && value.length <= 64 ? value : undefined;

export default function FeedbackPage({ searchParams }: { searchParams: Search }) {
  return (
    <Container className="max-w-3xl py-10 sm:py-14">
      <PageHeader
        eyebrow="Feedback"
        title="How did AgroCycle work for you?"
        back={{ href: routes.home, label: "home" }}
      >
        <p>
          It takes about a minute. Two ratings are needed; everything else is optional,
          and a skipped answer is kept as “not provided”, never as “no”.
        </p>
        <p>
          AgroCycle covers Iowa. If you do not farm or advise in Iowa, your feedback tells
          us how clear and usable the app is, not whether its Iowa agronomy is right. We
          keep the two apart, and we have not yet heard from an Iowa farmer or adviser.
        </p>
      </PageHeader>
      <div className="mt-8">
        {/* The field and comparison ids come from the URL, which is only known per request. */}
        <Suspense
          fallback={
            <div
              aria-busy
              className="h-96 animate-pulse rounded-[var(--radius-card)] bg-sunken"
            />
          }
        >
          <Form searchParams={searchParams} />
        </Suspense>
      </div>
    </Container>
  );
}

async function Form({ searchParams }: { searchParams: Search }) {
  const raw = await searchParams;
  return <FeedbackForm fieldId={one(raw.field)} analysisId={one(raw.analysis)} />;
}
