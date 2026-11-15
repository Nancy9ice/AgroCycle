"use client";

import { useSyncExternalStore } from "react";

export const MOBILE_QUERY = "(max-width: 575px)";

function subscribe(onChange: () => void) {
  const query = window.matchMedia(MOBILE_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

/** True on phone-width screens. The server and first paint assume desktop, so hydration never mismatches. */
export function useIsMobile(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(MOBILE_QUERY).matches,
    () => false,
  );
}
