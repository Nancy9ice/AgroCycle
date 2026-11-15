import Image from "next/image";
import { ArrowRightIcon } from "@/components/icons/arrow-right-icon";
import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { demoFieldsRoute, routes } from "@/lib/routes";

export function Hero() {
  return (
    <section aria-labelledby="hero-title" className="home-hero">
      <Image
        src="/images/agrocycle-farmland.webp"
        alt=""
        fill
        preload
        sizes="100vw"
        className="home-hero-image"
      />
      <div className="home-hero-shade" aria-hidden />
      <Container className="home-container home-hero-content">
        <div className="home-hero-copy">
          <p className="home-eyebrow home-hero-eyebrow">
            <span /> NASA Space Apps 2026 · Field Shift
          </p>
          <h1 id="hero-title">
            Your land.
            <br />
            <em>New possibilities.</em>
          </h1>
          <p className="home-hero-description">
            Explore what a different crop rotation could mean for your field. NASA data,
            local evidence and your priorities, brought together.
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
          <p className="home-hero-assurance">
            No sign-up. Just a little curiosity about your land.
          </p>
        </div>
        <div className="home-hero-bottom">
          <a href="#decision" className="home-scroll-link">
            <span className="home-scroll-icon">
              <ArrowRightIcon className="size-4 rotate-90" />
            </span>{" "}
            A new perspective starts here
          </a>
          <p>
            Story &amp; Boone Counties, Iowa
            <br />
            <span>Illustrative landscape · AI-generated</span>
          </p>
        </div>
      </Container>
    </section>
  );
}
