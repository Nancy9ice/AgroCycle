"use client";

import { Suspense, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { AppNav } from "@/components/layout/app-nav";
import { routes } from "@/lib/routes";

/**
 * The landing page keeps its own header (`home`); every other page gets the fixed app navigation.
 * The Suspense fallback holds the nav's height, so nothing jumps while the URL is read.
 */
export function SiteNav({ home }: { home: ReactNode }) {
  return (
    <Suspense fallback={<div aria-hidden className="h-16" />}>
      <NavForPath home={home} />
    </Suspense>
  );
}

function NavForPath({ home }: { home: ReactNode }) {
  const pathname = usePathname();
  if (pathname === routes.home) return home;
  return <AppNav />;
}
