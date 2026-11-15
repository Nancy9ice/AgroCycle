import { CtaSection } from "@/features/home/cta-section";
import { DecisionSection } from "@/features/home/decision-section";
import { EvidenceSection } from "@/features/home/evidence-section";
import { Hero } from "@/features/home/hero";
import { HonestySection } from "@/features/home/honesty-section";
import { HowItWorksSection } from "@/features/home/how-it-works-section";
import { StrategiesSection } from "@/features/home/strategies-section";
import "@/features/home/home.css";

export default function HomePage() {
  return (
    <div className="landing-page">
      <Hero />
      <DecisionSection />
      <StrategiesSection />
      <HowItWorksSection />
      <HonestySection />
      <EvidenceSection />
      <CtaSection />
    </div>
  );
}
