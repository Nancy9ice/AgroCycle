"use client";

import { useEffect, useRef, type ReactNode } from "react";

/** Keeps the navigation reachable while scrolling back through the landing page. */
export function ScrollHeader({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const header = ref.current;
    if (!header) return;

    let previousY = Math.max(0, window.scrollY);
    let frame = 0;

    const update = () => {
      frame = 0;
      const y = Math.max(0, window.scrollY);
      header.dataset.scrolled = String(y > 80);

      if (y <= 128) {
        header.dataset.hidden = "false";
        previousY = y;
      } else if (Math.abs(y - previousY) >= 8) {
        header.dataset.hidden = String(y > previousY);
        previousY = y;
      }
    };
    const onScroll = () => {
      if (!frame) frame = window.requestAnimationFrame(update);
    };

    update();
    header.dataset.scrollReady = "true";
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <header
      ref={ref}
      data-site-header
      data-scrolled="false"
      data-hidden="false"
      className={className}
    >
      {children}
    </header>
  );
}
