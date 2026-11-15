import { LogoMark } from "@/components/icons/logo-mark";
import { ScrollStackSection } from "@/components/scroll-stack/scroll-stack-section";
import { howItWorksCards } from "@/features/home/content";
import { howItWorksIllustrations } from "./how-it-works-illustrations";

export function HowItWorksSection() {
  return (
    <ScrollStackSection
      id="how-it-works"
      className="home-workflow"
      intro={{
        number: "03",
        eyebrow: "A clear path forward",
        heading: (
          <>
            From your field
            <br />
            to your <em>next step.</em>
          </>
        ),
        paragraph:
          "Bring your questions. We’ll help you see the options, one step at a time.",
        mark: <LogoMark />,
      }}
      cards={howItWorksCards}
      illustrations={howItWorksIllustrations}
    />
  );
}
