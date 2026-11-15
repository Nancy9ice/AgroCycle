"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import type { EvidenceSource } from "./content";
import "./evidence-scroll.css";

/**
 * A list that pins to the screen while you scroll. Each source takes a turn: its row opens and its photo
 * fades in. Scroll position is read in one rAF-throttled listener; React state changes only when the
 * active source does, so scrolling stays smooth. Clicking a row scrolls to that source.
 * Keep overflow hidden/clip off every ancestor of `.ev-stage`, or sticky stops working.
 */
export function EvidenceScroll({ sources }: { sources: readonly EvidenceSource[] }) {
  const runwayRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(0);
  const count = sources.length;

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
      stage.style.setProperty("--ev-progress", progress.toFixed(4));
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

  const goTo = (index: number) => {
    const runway = runwayRef.current;
    const stage = stageRef.current;
    if (!runway || !stage) return;
    const top = parseFloat(getComputedStyle(stage).top) || 0;
    const range = runway.offsetHeight - stage.offsetHeight;
    const runwayTop = runway.getBoundingClientRect().top + window.scrollY;
    window.scrollTo({ top: runwayTop - top + ((index + 0.5) / count) * range });
  };

  return (
    <div
      ref={runwayRef}
      className="ev-runway"
      style={{ "--ev-count": count } as React.CSSProperties}
    >
      <div ref={stageRef} className="ev-stage">
        <ol className="ev-list">
          {sources.map((source, index) => (
            <li key={source.name} data-active={index === active ? "" : undefined}>
              <button
                type="button"
                className="ev-row"
                aria-current={index === active ? "true" : undefined}
                onClick={() => goTo(index)}
              >
                <span className="home-small-number">0{index + 1}</span>
                <span className="ev-row-title">
                  <span className="ev-provider">{source.provider}</span>
                  <span className="ev-name">{source.name}</span>
                </span>
              </button>
              <div className="ev-detail">
                <div>
                  <p className="ev-role">{source.role}</p>
                  <div className="ev-meta">
                    <EvidenceBadge type={source.evidence} />
                    <span>{source.scale}</span>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ol>

        <div className="ev-media">
          {sources.map((source, index) => (
            <Image
              key={source.image.src}
              src={source.image.src}
              alt={index === active ? source.image.alt : ""}
              fill
              sizes="(max-width: 767px) 100vw, 55vw"
              className="ev-photo"
              data-active={index === active ? "" : undefined}
            />
          ))}
          <p className="ev-caption" aria-hidden>
            <span>
              {sources[active].provider} · {sources[active].name}
            </span>
            <span>Illustrative photo</span>
          </p>
        </div>
      </div>
    </div>
  );
}
