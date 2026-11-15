"use client";

import { useEffect, useRef, type ReactNode } from "react";

interface ScrollRevealProps {
  children: ReactNode;
  className?: string;
  delay?: number;
}

/** Animates on entry without hiding server-rendered or no-JavaScript content. */
export function ScrollReveal({ children, className, delay = 0 }: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element || !("IntersectionObserver" in window) || !element.animate) return;

    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let animation: Animation | undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;
        observer.unobserve(element);
        if (motion.matches || element.contains(document.activeElement)) return;
        animation = element.animate(
          [
            { opacity: 0, transform: "translateY(24px)" },
            { opacity: 1, transform: "translateY(0)" },
          ],
          {
            duration: 850,
            delay,
            easing: "cubic-bezier(0.16, 1, 0.3, 1)",
            fill: "backwards",
          },
        );
      },
      { threshold: 0.08, rootMargin: "0px 0px -24px 0px" },
    );

    const reveal = () => {
      animation?.cancel();
      observer.unobserve(element);
    };
    const onMotionChange = () => {
      if (motion.matches) animation?.cancel();
    };

    observer.observe(element);
    element.addEventListener("focusin", reveal);
    motion.addEventListener("change", onMotionChange);
    return () => {
      observer.disconnect();
      animation?.cancel();
      element.removeEventListener("focusin", reveal);
      motion.removeEventListener("change", onMotionChange);
    };
  }, [delay]);

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}
