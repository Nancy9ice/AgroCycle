"use client";

import Link from "next/link";
import { motion, useTransform, type MotionValue } from "framer-motion";
import { clamp, PEEK } from "./timeline";
import type { StackCardData } from "./types";

interface ScrollStackCardProps {
  card: StackCardData;
  index: number;
  count: number;
  isMobile: boolean;
  /** The rounded active index. Only the current card is reachable by keyboard. */
  current: number;
  leftOpacity: MotionValue<number>;
  activeIndex: MotionValue<number>;
}

const lerp = (from: number, to: number, t: number) => from + (to - from) * t;

/** Desktop: 0 = waiting below, peeking; 1 = in place. */
function desktopProgress(index: number, active: number, left: number) {
  if (left < 1) return index === 0 ? Math.max(0, (left - 0.5) / 0.5) : 0;
  const diff = active - index;
  if (diff < -PEEK) return 0;
  if (diff >= 0) return 1;
  return (diff + PEEK) / PEEK;
}

/** Mobile: translateY in percent. 95 = waiting, 0 = in place, -110 = exited upward. */
function mobileOffset(index: number, active: number, left: number) {
  if (left < 1) return index === 0 ? lerp(95, 0, Math.max(0, (left - 0.5) / 0.5)) : 95;
  const diff = active - index;
  if (diff < -PEEK) return 95;
  if (diff < 0) return lerp(95, 0, (diff + PEEK) / PEEK);
  if (diff < 0.7) return lerp(0, -110, diff / 0.7);
  return -110;
}

export function ScrollStackCard({
  card,
  index,
  isMobile,
  current,
  leftOpacity,
  activeIndex,
}: ScrollStackCardProps) {
  const progress = useTransform([activeIndex, leftOpacity], ([active, left]: number[]) =>
    clamp(desktopProgress(index, active, left), 0, 1),
  );
  const top = useTransform(progress, [0, 1], ["95%", "0%"]);
  const left = useTransform(progress, [0, 1], [`${index * 80}px`, `${index * 10}px`]);

  const offset = useTransform([activeIndex, leftOpacity], ([active, lft]: number[]) =>
    mobileOffset(index, active, lft),
  );
  const y = useTransform(offset, (value) => `${value}%`);

  const style = isMobile
    ? { y }
    : { top, left, width: `calc(100% - ${index * 10}px)`, zIndex: index + 1 };

  return (
    <motion.article
      className="ss-card"
      style={{ ...style, zIndex: index + 1 }}
      inert={current !== index}
    >
      {card.kicker ? <p className="ss-card-kicker">{card.kicker}</p> : null}
      <h3 className="ss-card-title">{card.title}</h3>
      <div className="ss-card-content">
        {card.desc ? <p>{card.desc}</p> : null}
        {card.desc1 ? <p>{card.desc1}</p> : null}
        {card.list ? (
          <ul>
            {card.list.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : null}
      </div>
      {card.pills?.length ? (
        <div className="ss-pills">
          {card.pills.map((pill, pillIndex) =>
            pill.href ? (
              <Link
                key={pill.label}
                href={pill.href}
                className="ss-pill"
                data-primary={pillIndex === 0 ? "" : undefined}
              >
                {pill.label}
              </Link>
            ) : (
              <span key={pill.label} className="ss-pill ss-pill-tag">
                {pill.label}
              </span>
            ),
          )}
        </div>
      ) : null}
    </motion.article>
  );
}
