"use client";

import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { parseAnswers, serializeAnswers } from "./answers-codec";
import type { Answers, QuestionId } from "./questions";

/**
 * Answers are held in state, so quick successive clicks never overwrite each other, and
 * mirrored into the URL so a result can be shared and survives a reload. The URL is read once,
 * when the form mounts.
 */
export function useAnswers() {
  const searchParams = useSearchParams();
  const [answers, setAnswers] = useState<Answers>(() =>
    parseAnswers(new URLSearchParams(searchParams.toString())),
  );

  useEffect(() => {
    const query = serializeAnswers(answers).toString();
    const target = query
      ? `${window.location.pathname}?${query}`
      : window.location.pathname;
    if (target !== `${window.location.pathname}${window.location.search}`) {
      window.history.replaceState(null, "", target);
    }
  }, [answers]);

  const setAnswer = useCallback((id: QuestionId, value: string | undefined) => {
    setAnswers((previous) => {
      const next: Answers = { ...previous };
      if (value === undefined) delete next[id];
      else next[id] = value;
      return next;
    });
  }, []);

  return { answers, setAnswer };
}
