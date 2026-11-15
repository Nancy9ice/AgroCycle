import type { ReactNode } from "react";
import { Container } from "@/components/ui/container";
import { ScrollReveal } from "@/components/ui/scroll-reveal";
import { cn } from "@/lib/cn";

interface HomeSectionProps {
  id: string;
  number: string;
  eyebrow: string;
  title: ReactNode;
  intro?: string;
  children: ReactNode;
  className?: string;
}

export function HomeSection({
  id,
  number,
  eyebrow,
  title,
  intro,
  children,
  className,
}: HomeSectionProps) {
  return (
    <section
      id={id}
      aria-labelledby={`${id}-title`}
      className={cn("home-section", className)}
    >
      <Container className="home-container">
        <ScrollReveal>
          <div className="home-section-label">
            <span>{number}</span>
            <span>{eyebrow}</span>
          </div>
          <header className="home-section-header">
            <h2 id={`${id}-title`} className="home-heading">
              {title}
            </h2>
            {intro ? <p className="home-section-intro">{intro}</p> : null}
          </header>
        </ScrollReveal>
        {children}
      </Container>
    </section>
  );
}
