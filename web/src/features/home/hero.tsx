import Image from "next/image";
import { ArrowRightIcon } from "@/components/icons/arrow-right-icon";
import { ButtonLink } from "@/components/ui/button";
import { demoFieldsRoute, routes } from "@/lib/routes";
import "./hero.css";

export function Hero() {
  return (
    <section aria-labelledby="hero-title" className="home-hero home-split-hero">
      <div className="home-split-panel home-split-left">
        <Image
          src="/images/hero-left-unsplash.webp"
          alt=""
          fill
          loading="eager"
          fetchPriority="high"
          sizes="(max-width: 767px) 100vw, 50vw"
          className="home-split-photo home-split-photo-left"
        />
        <div className="home-split-overlay" aria-hidden />
        <div className="home-split-copy home-hero-copy">
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
      </div>
      <div className="home-split-panel home-split-right">
        <Image
          src="/images/hero-right-unsplash.webp"
          alt="A white barn with a red roof in warm evening light."
          fill
          loading="eager"
          sizes="(max-width: 767px) 100vw, 50vw"
          className="home-split-photo home-split-photo-right"
        />
        <div className="home-split-overlay" aria-hidden />
        <div className="home-split-caption">
          <span className="home-eyebrow">Rooted in the real world</span>
          <p>
            A fresh perspective.
            <br />
            For your next season.
          </p>
        </div>
      </div>
    </section>
  );
}
