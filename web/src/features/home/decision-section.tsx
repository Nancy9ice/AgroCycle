import { ScrollReveal } from "@/components/ui/scroll-reveal";
import { decisionPoints } from "@/features/home/content";
import { HomePhoto } from "./home-photo";
import { HomeSection } from "./home-section";

export function DecisionSection() {
  return (
    <HomeSection
      id="decision"
      number=""
      eyebrow=""
      title={
        <>
          The next chapter
          <br />
          for your field.
        </>
      }
      intro="Stay with corn and soybeans, or make room for something different? Explore the evidence for your land before making a change."
    >
      <ScrollReveal>
        <HomePhoto
          src="/images/fields/sunset-field.jpg"
          alt="A harvested field at sunset, with long rows running to the horizon."
          className="home-photo-wide"
          sizes="(max-width: 767px) 100vw, 1400px"
        />
      </ScrollReveal>
      <div className="home-decision-bottom">
        <ol className="home-decision-points">
          {decisionPoints.map((point, index) => (
            <li key={point.title}>
              <ScrollReveal delay={index * 90}>
                <span className="home-small-number">0{index + 1}</span>
                <h3>{point.title}</h3>
                <p>{point.body}</p>
              </ScrollReveal>
            </li>
          ))}
        </ol>
        <ScrollReveal>
          <div className="home-pilot-note">
            <span className="home-eyebrow">Rooted in Iowa</span>
            <p>
              Our first chapter: corn–soybean fields in Story and Boone Counties. A
              focused pilot, with the evidence and its limits always in view.
            </p>
          </div>
        </ScrollReveal>
      </div>
    </HomeSection>
  );
}
