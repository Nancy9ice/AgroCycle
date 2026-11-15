import Image from "next/image";
import { ArrowRightIcon } from "@/components/icons/arrow-right-icon";
import { NasaLogo } from "@/components/icons/nasa-logo";
import { ButtonLink } from "@/components/ui/button";
import { demoFieldsRoute, routes } from "@/lib/routes";
import { cn } from "@/lib/cn";
import "./hero.css";

export function Hero({
  layout = "single",
  image = "second",
}: {
  layout?: "single" | "split";
  image?: "first" | "second";
} = {}) {
  const split = layout === "split";
  return (
    <section
      aria-labelledby="hero-title"
      className={cn("home-hero home-split-hero", !split && "home-single-hero")}
    >
      <div className="home-split-panel home-split-left">
        <Image
          src={
            split || image === "first"
              ? "/images/hero-left-unsplash.webp"
              : "/images/hero-right-unsplash.webp"
          }
          alt=""
          fill
          loading="eager"
          fetchPriority="high"
          sizes={split ? "(max-width: 767px) 100vw, 50vw" : "100vw"}
          className="home-split-photo home-split-photo-left"
        />
        <div className="home-split-overlay" aria-hidden />
        <div className="home-split-copy home-hero-copy">
          <p className="home-eyebrow home-hero-eyebrow">
            {/* <NasaLogo /> */}
            NASA Space Apps 2026 · Field Shift
          </p>
          <h1 id="hero-title">
            Your land.
            <br />
            <em>New possibilities.</em>
          </h1>
          <p className="home-hero-description">
            Explore what a different crop rotation could mean for your field and the
            seasons ahead. AgroCycle brings NASA environmental data, local soil and crop
            information, research evidence and your farming priorities into one clear
            picture.
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
          <p className="home-hero-assurance mt-7">
            No sign-up. Just a little curiosity about your land.
          </p>
        </div>
      </div>
      {split ? (
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
      ) : null}
    </section>
  );
}
