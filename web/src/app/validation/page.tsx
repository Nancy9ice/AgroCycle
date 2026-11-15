import type { Metadata } from "next";
import { Container } from "@/components/ui/container";
import { ValidationScreen } from "@/features/validation/validation-screen";

export const metadata: Metadata = {
  title: "How we checked this",
  description:
    "What has been checked in AgroCycle, by which kind of check, and what has not.",
};

export default function ValidationPage() {
  return (
    <Container className="max-w-5xl py-6 sm:py-8">
      <ValidationScreen />
    </Container>
  );
}
