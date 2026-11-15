import { EvidenceBadge } from "@/components/evidence/evidence-badge";
import { ScrollReveal } from "@/components/ui/scroll-reveal";
import { evidenceSources } from "@/features/home/content";
import { HomeSection } from "./home-section";

export function EvidenceSection() {
  return (
    <HomeSection
      id="evidence"
      number="05"
      eyebrow="Grounded in evidence"
      title={
        <>
          A view from above.
          <br />
          <em>Evidence from the ground.</em>
        </>
      }
      intro="A satellite image and a soil survey tell different stories. We bring them together, while making each source, scale and limitation clear."
      className="home-evidence"
    >
      <ul className="home-source-list">
        {evidenceSources.map((source, index) => (
          <li key={source.name}>
            <ScrollReveal delay={index * 40} className="home-source-row">
              <p className="home-source-provider">
                <span className="home-small-number">0{index + 1}</span>
                {source.provider}
              </p>
              <div>
                <h3>{source.name}</h3>
                <p className="home-source-role">{source.role}</p>
              </div>
              <div className="home-source-meta">
                <EvidenceBadge type={source.evidence} />
                <p>{source.scale}</p>
              </div>
            </ScrollReveal>
          </li>
        ))}
      </ul>
    </HomeSection>
  );
}
