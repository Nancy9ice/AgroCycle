"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { initialHeaderState, nextHeaderState } from "./scroll-header-state";

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

    let state = initialHeaderState(window.scrollY);
    let frame = 0;
    let touchY = 0;

    const closeMenu = () => {
      header.querySelectorAll<HTMLDetailsElement>("details[open]").forEach((menu) => {
        menu.open = false;
      });
    };
    const apply = () => {
      header.dataset.mode = state.mode;
      if (state.mode === "hidden") closeMenu();
    };
    const hide = () => {
      if (window.scrollY <= 80) return;
      state = { y: Math.max(0, window.scrollY), upwardDistance: 0, mode: "hidden" };
      apply();
    };

    const update = () => {
      frame = 0;
      state = nextHeaderState(state, window.scrollY);
      apply();
    };
    const onScroll = () => {
      if (window.scrollY > state.y) hide();
      if (!frame) frame = window.requestAnimationFrame(update);
    };
    const onWheel = (event: WheelEvent) => {
      if (event.deltaY > 0) hide();
    };
    const onTouchStart = (event: TouchEvent) => {
      touchY = event.touches[0]?.clientY ?? 0;
    };
    const onTouchMove = (event: TouchEvent) => {
      const y = event.touches[0]?.clientY ?? touchY;
      if (y < touchY) hide();
      touchY = y;
    };
    const onLink = (event: MouseEvent) => {
      if (event.target instanceof Element && event.target.closest("a")) closeMenu();
    };

    apply();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    window.addEventListener("wheel", onWheel, { passive: true });
    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchmove", onTouchMove, { passive: true });
    header.addEventListener("click", onLink);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("touchstart", onTouchStart);
      window.removeEventListener("touchmove", onTouchMove);
      header.removeEventListener("click", onLink);
      window.cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <header ref={ref} data-site-header data-mode="top" className={className}>
      {children}
    </header>
  );
}
