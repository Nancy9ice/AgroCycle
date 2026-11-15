import { LogoMark } from "@/components/icons/logo-mark";
import { ScrollStackSection } from "@/components/scroll-stack/scroll-stack-section";
import { honestyCards } from "@/features/home/content";
import { honestyIllustrations } from "./honesty-illustrations";

export function HonestySection() {
  return (
    <ScrollStackSection
      id="honesty"
      intro={{
        number: "04",
        eyebrow: "Honest by nature",
        heading: (
          <>
            Clarity, even when
            <br />
            it’s <em>uncertain.</em>
          </>
        ),
        paragraph:
          "A useful answer doesn’t always pick a winner. We show what the evidence supports, where the trade-offs are, and when we simply don’t know.",
        mark: <LogoMark />,
      }}
      cards={honestyCards}
      illustrations={honestyIllustrations}
    />
  );
}
