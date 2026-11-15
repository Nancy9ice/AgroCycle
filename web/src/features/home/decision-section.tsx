import { decisionPoints } from "@/features/home/content";
import { DecisionScroll } from "./decision-scroll";
import { HomeSection } from "./home-section";

export function DecisionSection() {
  return (
    <HomeSection
      id="decision"
      title={
        <>
          The next chapter
          <br />
          for your field.
        </>
      }
      intro="Stay with corn and soybeans, or make room for something different? Explore the evidence for your land before making a change."
    >
      <DecisionScroll
        points={decisionPoints}
        note={
          <>
            <span className="home-eyebrow">Rooted in Iowa</span>
            <p>
              Our first chapter: corn–soybean fields in Story and Boone Counties. A
              focused pilot, with the evidence and its limits always in view.
            </p>
          </>
        }
      />
    </HomeSection>
  );
}
