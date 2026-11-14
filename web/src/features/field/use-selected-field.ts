"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { PRIMARY_FIELD_ID, getFieldById } from "./data";
import type { DemoField } from "./types";

/**
 * The selected field lives in the URL (`?field=<id>`), so it can be shared and survives a
 * reload. The primary demo field is the default. An unknown id falls back to it and is reported.
 */
export function useSelectedField() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const requestedId = searchParams.get("field");
  const requested = getFieldById(requestedId);
  const selected = (requested ?? getFieldById(PRIMARY_FIELD_ID)) as DemoField;
  const unknownRequestedId = requestedId && !requested ? requestedId : null;

  const select = useCallback(
    (id: string) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("field", id);
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  return { selected, select, unknownRequestedId };
}
