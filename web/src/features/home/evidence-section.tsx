import { evidenceSources } from "@/features/home/content";
import { EvidenceScroll } from "./evidence-scroll";
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
      <EvidenceScroll sources={evidenceSources} />
    </HomeSection>
  );
}
