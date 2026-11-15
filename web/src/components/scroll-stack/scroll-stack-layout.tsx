"use client";

import { useState, type ReactNode } from "react";
import {
  motion,
  useMotionValueEvent,
  useTransform,
  type MotionValue,
} from "framer-motion";
import { ScrollStackCard } from "./scroll-stack-card";
import { clamp } from "./timeline";
import type { StackCardData } from "./types";
import { useIsMobile } from "./use-is-mobile";

interface ScrollStackLayoutProps {
  cards: readonly StackCardData[];
  illustrations: readonly ReactNode[];
  leftOpacity: MotionValue<number>;
  activeIndex: MotionValue<number>;
}

/** Cross-fades the illustration that belongs to the current card. */
function ActiveImage({
  index,
  current,
  children,
}: {
  index: number;
  current: number;
  children: ReactNode;
}) {
  return (
    <motion.div
      className="ss-image"
      initial={false}
      animate={{ opacity: current === index ? 1 : 0 }}
      transition={{ duration: 0.4, ease: "easeInOut" }}
      aria-hidden
    >
      {children}
    </motion.div>
  );
}

export function ScrollStackLayout({
  cards,
  illustrations,
  leftOpacity,
  activeIndex,
}: ScrollStackLayoutProps) {
  const isMobile = useIsMobile();
  const last = cards.length - 1;
  // Keep the waiting cards' edges out of the intro frame until the illustration starts to appear.
  const stackOpacity = useTransform(leftOpacity, [0, 0.2], [0, 1]);
  // The only React state: which illustration (and which card is interactive) is current.
  const [imgIndex, setImgIndex] = useState(0);

  useMotionValueEvent(activeIndex, "change", (value) => {
    const next = Math.round(clamp(value, 0, last));
    setImgIndex((previous) => (previous === next ? previous : next));
  });

  return (
    <div className="ss-layout" data-mobile={isMobile ? "" : undefined}>
      <motion.div className="ss-left" style={{ opacity: leftOpacity }}>
        {illustrations.map((illustration, index) => (
          <ActiveImage key={index} index={index} current={imgIndex}>
            {illustration}
          </ActiveImage>
        ))}
      </motion.div>
      <motion.div className="ss-right" style={{ opacity: stackOpacity }}>
        {cards.map((card, index) => (
          <ScrollStackCard
            // Remount when the variant changes so one variant's inline styles never leak into the other.
            key={`${card.title}-${isMobile ? "m" : "d"}`}
            card={card}
            index={index}
            count={cards.length}
            isMobile={isMobile}
            current={imgIndex}
            leftOpacity={leftOpacity}
            activeIndex={activeIndex}
          />
        ))}
      </motion.div>
    </div>
  );
}
