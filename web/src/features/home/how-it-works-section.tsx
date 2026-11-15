import { Container } from "@/components/ui/container";
import { ScrollReveal } from "@/components/ui/scroll-reveal";
import { flowSteps } from "@/features/home/content";

export function HowItWorksSection() {
  return (
    <section
      id="how-it-works"
      aria-labelledby="how-it-works-title"
      className="home-section home-workflow"
    >
      <Container className="home-container home-workflow-grid">
        <ScrollReveal className="home-workflow-intro">
          <div className="home-section-label">
            <span>03</span>
            <span>A clear path forward</span>
          </div>
          <h2 id="how-it-works-title" className="home-heading">
            From your field
            <br />
            to your <em>next step.</em>
          </h2>
          <p>Bring your questions. We’ll help you see the options, one step at a time.</p>
          <span className="home-workflow-decoration" aria-hidden>
            01—05
          </span>
        </ScrollReveal>
        <ol className="home-steps">
          {flowSteps.map((step, index) => (
            <li key={step.title}>
              <ScrollReveal delay={index * 45} className="home-step">
                <span className="home-step-number">0{index + 1}</span>
                <div>
                  <h3>{step.title}</h3>
                  <p>{step.body}</p>
                </div>
              </ScrollReveal>
            </li>
          ))}
        </ol>
      </Container>
    </section>
  );
}
