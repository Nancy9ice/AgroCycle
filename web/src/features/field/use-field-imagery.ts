"use client";

import { useEffect, useState } from "react";
import { imageryUrl, parseImagery, type FieldImagery } from "./imagery";

export type ImageryState =
  | { status: "loading" }
  | { status: "none" }
  | { status: "error" }
  | { status: "ready"; imagery: FieldImagery };

const cache = new Map<string, FieldImagery | null>();

/**
 * Whether the selected field has an aerial photo. "None" and "error" both hide the photo toggle; only
 * "error" says why, because a broken service must not look the same as a field without a photo.
 */
export function useFieldImagery(fieldId: string | undefined): ImageryState {
  const [result, setResult] = useState<{ id: string; state: ImageryState } | null>(null);

  useEffect(() => {
    if (!fieldId) return;
    if (cache.has(fieldId)) return;
    const controller = new AbortController();
    fetch(imageryUrl(fieldId), { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(String(response.status));
        const imagery = parseImagery(await response.json());
        cache.set(fieldId, imagery);
        setResult({
          id: fieldId,
          state: imagery ? { status: "ready", imagery } : { status: "none" },
        });
      })
      .catch((error: unknown) => {
        if ((error as Error).name === "AbortError") return;
        setResult({ id: fieldId, state: { status: "error" } });
      });
    return () => controller.abort();
  }, [fieldId]);

  if (!fieldId) return { status: "none" };
  if (cache.has(fieldId)) {
    const imagery = cache.get(fieldId) ?? null;
    return imagery ? { status: "ready", imagery } : { status: "none" };
  }
  return result?.id === fieldId ? result.state : { status: "loading" };
}
