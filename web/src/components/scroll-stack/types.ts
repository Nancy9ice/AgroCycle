import type { ReactNode } from "react";

export interface StackPill {
  label: string;
  /** Pills with an `href` are links; without one they are plain tags. */
  href?: string;
}

/** One card in the stack. All text is data so a section only supplies content. */
export interface StackCardData {
  title: string;
  kicker?: string;
  desc?: string;
  desc1?: string;
  list?: readonly string[];
  pills?: readonly StackPill[];
}

export interface ScrollStackIntro {
  /** Small label above the heading, e.g. "03" and "A clear path forward". */
  number: string;
  eyebrow: string;
  heading: ReactNode;
  paragraph: string;
  /** Centre-of-frame mark. */
  mark: ReactNode;
}
