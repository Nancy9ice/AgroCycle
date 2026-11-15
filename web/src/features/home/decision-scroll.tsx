"use client";

import Image from "next/image";
import type { ReactNode } from "react";
import type { decisionPoints } from "./content";
import { usePinnedProgress } from "./use-pinned-progress";
import "./decision-scroll.css";

type DecisionPoint = (typeof decisionPoints)[number];

/**
 * The three questions, one at a time. The section pins while you scroll; each question brings its own
 * photo, heading and sentence in on the right, and the big number on the left counts along.
 */
export function DecisionScroll({
  points,
  note,
}: {
  points: readonly DecisionPoint[];
  /** Sits under the big number, so it stays on screen while the section is pinned. */
  note?: ReactNode;
}) {
  const count = points.length;
  const { runwayRef, stageRef, active } = usePinnedProgress(count);

  return (
    <div
      ref={runwayRef}
      className="dc-runway"
      style={{ "--dc-count": count } as React.CSSProperties}
    >
      <div ref={stageRef} className="dc-stage">
        <div className="dc-side">
          <div className="dc-numerals" aria-hidden>
            {points.map((point, index) => (
              <span key={point.title} data-active={index === active ? "" : undefined}>
                0{index + 1}
              </span>
            ))}
          </div>
          {note ? <div className="dc-note">{note}</div> : null}
        </div>

        <div className="dc-content">
          <div className="dc-media">
            {points.map((point, index) => (
              <Image
                key={point.image.src}
                src={point.image.src}
                alt={index === active ? point.image.alt : ""}
                fill
                sizes="(max-width: 767px) 100vw, 60vw"
                className="dc-photo"
                data-active={index === active ? "" : undefined}
              />
            ))}
          </div>
          <div className="dc-text">
            {points.map((point, index) => (
              <div key={point.title} data-active={index === active ? "" : undefined}>
                <h3>{point.title}</h3>
                <p>{point.body}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
