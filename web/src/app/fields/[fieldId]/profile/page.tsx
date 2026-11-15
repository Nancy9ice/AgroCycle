import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { connection } from "next/server";
import { Suspense } from "react";
import { Container } from "@/components/ui/container";
import { demoFields, getFieldById } from "@/features/field/data";
import { getFieldProfile } from "@/features/profile/get-field-profile";
import { ProfileScreen } from "@/features/profile/profile-screen";

export const metadata: Metadata = {
  title: "Your field",
  description:
    "What is known about this field: crop history, weather, how green it is through the year, and the soil, each with where it came from.",
};

export function generateStaticParams() {
  return demoFields.map((field) => ({ fieldId: field.id }));
}

export default function ProfilePage({
  params,
}: {
  params: Promise<{ fieldId: string }>;
}) {
  return (
    <Container className="max-w-[90rem] py-6 sm:py-8">
      {/* Route params are read inside Suspense so navigation can show the shell instantly. */}
      <Suspense
        fallback={
          <div
            aria-busy
            className="h-96 animate-pulse rounded-[var(--radius-card)] bg-sunken"
          />
        }
      >
        <Profile params={params} />
      </Suspense>
    </Container>
  );
}

async function Profile({ params }: { params: Promise<{ fieldId: string }> }) {
  const { fieldId } = await params;
  // Always render per request. The API's answer changes when the data pipeline runs, and a page built at
  // deploy time would freeze whatever was true then (including "no API configured"). The profile is cheap.
  await connection();
  const field = getFieldById(fieldId);
  const profile = await getFieldProfile(fieldId);
  if (!field || !profile) notFound();

  return <ProfileScreen field={field} profile={profile} />;
}
