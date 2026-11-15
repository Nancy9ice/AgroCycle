import { CloseIcon } from "@/components/icons/close-icon";
import { ScrollReveal } from "@/components/ui/scroll-reveal";
import { outcomes, wontClaim } from "@/features/home/content";
import { HomePhoto } from "./home-photo";
import { HomeSection } from "./home-section";

export function HonestySection() {
  return (
    <HomeSection
      id="honesty"
      number="04"
      eyebrow="Honest by nature"
      title={
        <>
          Clarity, even when
          <br />
          it’s <em>uncertain.</em>
        </>
      }
      intro="A useful answer doesn’t always pick a winner. We show what the evidence supports, where the trade-offs are, and when we simply don’t know."
    >
      <ScrollReveal>
        <HomePhoto
          src="/images/fields/barn.jpg"
          alt="A red barn at the edge of a green field, with autumn trees behind."
          className="home-photo-wide"
          sizes="(max-width: 767px) 100vw, 1400px"
        />
      </ScrollReveal>
      <ul className="home-outcomes">
        {outcomes.map((outcome, index) => (
          <li key={outcome.title}>
            <ScrollReveal delay={index * 90} className="home-outcome">
              <span
                aria-hidden
                className={`home-outcome-marker home-outcome-marker-${index}`}
              />
              <h3>{outcome.title}</h3>
              <p>{outcome.body}</p>
            </ScrollReveal>
          </li>
        ))}
      </ul>
      <ScrollReveal>
        <div className="home-boundaries">
          <h3>
            Some things we
            <br />
            won’t promise.
          </h3>
          <ul>
            {wontClaim.map((item) => (
              <li key={item}>
                <CloseIcon className="size-4 shrink-0 text-clay-700" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </ScrollReveal>
    </HomeSection>
  );
}
