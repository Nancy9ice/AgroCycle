"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Drives a "pinned" section: a tall runway holds a sticky stage, and scrolling the runway steps through
 * `count` items. Scroll is read in one rAF-throttled passive listener; React state changes only when the
 * active item does. Also sets `--pin-progress` (0 to 1) on the stage for CSS to use.
 * Keep overflow hidden/clip off every ancestor of the stage, or sticky stops working.
 */
export function usePinnedProgress(count: number) {
  const runwayRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(0);

  useEffect(() => {
    const runway = runwayRef.current;
    const stage = stageRef.current;
    if (!runway || !stage) return;
    let frame = 0;

    const measure = () => {
      frame = 0;
      const top = parseFloat(getComputedStyle(stage).top) || 0;
      const range = runway.offsetHeight - stage.offsetHeight;
      if (range <= 0) return;
      const progress = Math.min(
        1,
        Math.max(0, (top - runway.getBoundingClientRect().top) / range),
      );
      stage.style.setProperty("--pin-progress", progress.toFixed(4));
      setActive(Math.min(count - 1, Math.floor(progress * count)));
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(measure);
    };

    measure();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    return () => {
      if (frame) cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [count]);

  /** Scroll to the middle of an item's share of the runway. */
  const goTo = useCallback(
    (index: number) => {
      const runway = runwayRef.current;
      const stage = stageRef.current;
      if (!runway || !stage) return;
      const top = parseFloat(getComputedStyle(stage).top) || 0;
      const range = runway.offsetHeight - stage.offsetHeight;
      const runwayTop = runway.getBoundingClientRect().top + window.scrollY;
      window.scrollTo({ top: runwayTop - top + ((index + 0.5) / count) * range });
    },
    [count],
  );

  return { runwayRef, stageRef, active, goTo };
}
