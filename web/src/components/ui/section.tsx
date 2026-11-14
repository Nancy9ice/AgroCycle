import type { ReactNode } from "react";
import { Container } from "@/components/ui/container";
import { cn } from "@/lib/cn";

interface SectionProps {
  id: string;
  /** Short uppercase label above the heading. */
  eyebrow?: string;
  title: ReactNode;
  intro?: ReactNode;
  children: ReactNode;
  tone?: "paper" | "sunken" | "dark";
  className?: string;
}

const tones = {
  paper: "bg-paper text-ink",
  sunken: "bg-sunken text-ink",
  dark: "bg-forest-950 text-white",
} as const;

/** Standard page section: labelled landmark, consistent rhythm, optional heading block. */
export function Section({
  id,
  eyebrow,
  title,
  intro,
  children,
  tone = "paper",
  className,
}: SectionProps) {
  const titleId = `${id}-title`;
  const isDark = tone === "dark";

  return (
    <section
      id={id}
      aria-labelledby={titleId}
      className={cn("py-20 sm:py-28", tones[tone])}
    >
      <Container className={className}>
        <header className="max-w-3xl">
          {eyebrow ? (
            <p
              className={cn(
                "font-mono text-xs font-medium tracking-[0.14em] uppercase",
                isDark ? "text-forest-200" : "text-forest-600",
              )}
            >
              {eyebrow}
            </p>
          ) : null}
          <h2
            id={titleId}
            className="mt-3 font-display text-3xl leading-tight font-semibold tracking-tight text-balance sm:text-4xl"
          >
            {title}
          </h2>
          {intro ? (
            <p
              className={cn(
                "mt-5 text-lg leading-relaxed text-pretty",
                isDark ? "text-forest-100" : "text-ink-soft",
              )}
            >
              {intro}
            </p>
          ) : null}
        </header>
        <div className="mt-12 sm:mt-14">{children}</div>
      </Container>
    </section>
  );
}
