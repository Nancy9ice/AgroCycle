import { Logo } from "@/components/brand/logo";
import { Container } from "@/components/ui/container";
import { site } from "@/lib/site";

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-sunken">
      <Container className="grid gap-8 py-12 md:grid-cols-[1.2fr_1fr]">
        <div>
          <Logo />
          <p className="mt-4 max-w-md text-[0.9375rem] text-ink-soft">{site.tagline}</p>
        </div>
        <div className="space-y-3 text-sm text-ink-soft">
          <p>
            <strong className="font-semibold text-ink">
              Decision support, not a prescription.
            </strong>{" "}
            AgroCycle does not predict yield or profit. Talk to a local adviser before
            changing your rotation.
          </p>
          <p>
            Pilot area: {site.pilot}. Fields shown are demonstration polygons drawn by the
            team, not real farm boundaries.
          </p>
          <p>
            Built for the {site.challenge}. An independent project, not an official NASA
            product.
          </p>
        </div>
      </Container>
    </footer>
  );
}
