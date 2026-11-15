import Image from "next/image";
import { ArrowRightIcon } from "@/components/icons/arrow-right-icon";
import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { ScrollReveal } from "@/components/ui/scroll-reveal";
import { demoFieldsRoute, routes } from "@/lib/routes";

export function CtaSection() {
  return (
    <section aria-labelledby="cta-title" className="home-cta">
      <Image
        src="/images/agrocycle-farmland.webp"
        alt=""
        fill
        sizes="100vw"
        className="home-cta-image"
      />
      <div aria-hidden className="home-cta-shade" />
      <Container className="home-container">
        <ScrollReveal className="home-cta-content">
          <p className="home-eyebrow">There’s more to explore</p>
          <h2 id="cta-title" className="home-heading">
            See your field
            <br />
            <em>in a new light.</em>
          </h2>
          <p>
            Start with your land, tell us what matters, and explore your rotation options.
            A starting point for a conversation with your adviser.
          </p>
          <div className="home-actions">
            <ButtonLink href={routes.field} className="home-button-light">
              Explore your field <ArrowRightIcon className="size-4" />
            </ButtonLink>
            <ButtonLink
              href={demoFieldsRoute}
              variant="secondary"
              className="home-button-outline"
            >
              Try a demo first <span aria-hidden>↗</span>
            </ButtonLink>
          </div>
          <p className="home-cta-note">
            No account needed · Iowa pilot · Every number shows its source
          </p>
        </ScrollReveal>
      </Container>
    </section>
  );
}
