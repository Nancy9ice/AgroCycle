"use client";

import { useEffect, useId, useRef, type CSSProperties, type ReactNode } from "react";
import { motion, useMotionValue, useTransform } from "framer-motion";
import { ScrollStackLayout } from "./scroll-stack-layout";
import { clamp, TIMELINE } from "./timeline";
import type { ScrollStackIntro, StackCardData } from "./types";
import "./scroll-stack.css";

interface ScrollStackSectionProps {
  id: string;
  intro: ScrollStackIntro;
  cards: readonly StackCardData[];
  /** One illustration per card, cross-faded on the left while the cards stack on the right. */
  illustrations: readonly ReactNode[];
  className?: string;
}

/**
 * A "scroll runway": a tall wrapper holds a sticky, viewport-high panel. Scrolling the wrapper drives
 * the animation inside the panel instead of moving it; when the last card has landed the panel releases.
 *
 * Progress comes from our own scroll listener, not framer-motion's `useScroll`, which fights smooth-scroll
 * libraries. Every animation is a `useTransform` of that one value, so scrolling never re-renders React.
 * Do not put `overflow: hidden` on any ancestor of the sticky panel: it silently disables `position: sticky`.
 */
export function ScrollStackSection({
  id,
  intro,
  cards,
  illustrations,
  className,
}: ScrollStackSectionProps) {
  const headingId = useId();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const count = cards.length;

  const rawScrollY = useMotionValue(0);
  useEffect(() => {
    const update = () => rawScrollY.set(window.scrollY);
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update, { passive: true });
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [rawScrollY]);

  const scrollYProgress = useTransform(rawScrollY, () => {
    const wrapper = wrapperRef.current;
    if (!wrapper) return 0;
    const range = wrapper.offsetHeight - window.innerHeight;
    if (range <= 0) return 0;
    return clamp(-wrapper.getBoundingClientRect().top / range, 0, 1);
  });

  const firstFrameOpacity = useTransform(scrollYProgress, TIMELINE.introFadeOut, [1, 0]);
  const leftOpacity = useTransform(scrollYProgress, TIMELINE.illustrationFadeIn, [0, 1]);
  const activeIndex = useTransform(scrollYProgress, TIMELINE.cards, [0, count - 1]);

  return (
    <section
      id={id}
      aria-labelledby={headingId}
      ref={wrapperRef}
      className={`ss-runway ${className ?? ""}`}
      style={{ "--ss-count": count } as CSSProperties}
    >
      <div className="ss-sticky">
        <div className="ss-panel">
          <ScrollStackLayout
            cards={cards}
            illustrations={illustrations}
            leftOpacity={leftOpacity}
            activeIndex={activeIndex}
          />
          <motion.div
            className="ss-intro"
            style={{ opacity: firstFrameOpacity, willChange: "opacity" }}
          >
            <p className="ss-label">
              <span>{intro.number}</span>
              <span>{intro.eyebrow}</span>
            </p>
            <h2 id={headingId} className="ss-heading">
              {intro.heading}
            </h2>
            <div className="ss-mark" aria-hidden>
              {intro.mark}
            </div>
            <p className="ss-intro-text">{intro.paragraph}</p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
