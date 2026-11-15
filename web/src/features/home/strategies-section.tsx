import { RotationRibbon } from "@/components/rotation/rotation-ribbon";
import { ScrollReveal } from "@/components/ui/scroll-reveal";
import { strategies } from "@/domain/strategies";
import { HomePhoto } from "./home-photo";
import { HomeSection } from "./home-section";

const photos = {
  A: {
    src: "/images/fields/rows.jpg",
    alt: "Neat crop rows running across a field under a pale sky.",
  },
  B: {
    src: "/images/fields/grain.jpg",
    alt: "A close view of ripe oat and wheat grains.",
  },
  C: { src: "/images/agrocycle-farmland.webp", alt: "Rolling farmland in soft light." },
} as const;

export function StrategiesSection() {
  return (
    <HomeSection
      id="strategies"
      title={
        <>
          Different seasons.
          <br />
          <em>Different possibilities.</em>
        </>
      }
      intro="One familiar rotation. Two longer alternatives. Compare the systems studied in an Iowa field trial, with room for your farm’s reality."
      className="home-strategies"
    >
      <ul className="home-strategy-grid">
        {strategies.map((strategy, index) => (
          <li
            key={strategy.id}
            className={`home-strategy home-strategy-${strategy.id.toLowerCase()}`}
          >
            <ScrollReveal delay={index * 100} className="home-strategy-inner">
              <HomePhoto
                {...photos[strategy.id]}
                className="home-photo-card"
                sizes="(max-width: 767px) 100vw, 33vw"
              />
              <div className="home-strategy-top">
                <span className="home-eyebrow">Option {strategy.id}</span>
                <span className="home-strategy-kind">{strategy.kind}</span>
              </div>
              <p className="home-cycle">
                <span>{strategy.phases.length}</span> year cycle
              </p>
              <h3>{strategy.name}</h3>
              <p className="home-strategy-summary">{strategy.summary}</p>
              <RotationRibbon strategy={strategy} className="home-rotation" />
            </ScrollReveal>
          </li>
        ))}
      </ul>
      <ScrollReveal>
        <p className="home-footnote">
          Comparison scenarios, not recommendations. Based on the Marsden Farm experiment
          (Davis et al., 2012, PLOS ONE). One research farm’s results are not predictions
          for your field.
        </p>
      </ScrollReveal>
    </HomeSection>
  );
}
