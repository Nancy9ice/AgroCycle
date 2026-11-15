import { Logo } from "@/components/brand/logo";
import { homeNav } from "@/components/layout/nav-links";
import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { routes } from "@/lib/routes";

const navLink =
  "rounded-full px-3.5 py-2 text-[0.9375rem] font-medium text-ink-soft transition-colors hover:bg-forest-100 hover:text-forest-800";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-line/80 bg-paper/90 backdrop-blur print:hidden">
      <Container className="flex h-16 items-center justify-between gap-4">
        <Logo />

        <nav aria-label="Primary" className="hidden items-center gap-1 lg:flex">
          {homeNav.map((item) => (
            <a key={item.href} href={item.href} className={navLink}>
              {item.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <ButtonLink
            href={routes.field}
            className="hidden min-h-11 px-5 text-[0.9375rem] sm:inline-flex"
          >
            Add your field
          </ButtonLink>

          {/* Mobile menu: native <details>, so it works without JavaScript and by keyboard. */}
          <details className="group relative lg:hidden">
            <summary
              className="flex size-11 cursor-pointer list-none items-center justify-center rounded-full border border-line-strong bg-surface [&::-webkit-details-marker]:hidden"
              aria-label="Menu"
            >
              <svg
                viewBox="0 0 24 24"
                className="size-5"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                aria-hidden
              >
                <path className="group-open:hidden" d="M4 7h16M4 12h16M4 17h16" />
                <path className="hidden group-open:block" d="M6 6l12 12M18 6L6 18" />
              </svg>
            </summary>
            <nav
              aria-label="Primary mobile"
              className="absolute right-0 mt-3 flex w-72 flex-col gap-1 rounded-2xl border border-line bg-surface p-3 shadow-card"
            >
              {homeNav.map((item) => (
                <a key={item.href} href={item.href} className={`${navLink} py-3`}>
                  {item.label}
                </a>
              ))}
              <ButtonLink href={routes.field} className="mt-2">
                Add your field
              </ButtonLink>
            </nav>
          </details>
        </div>
      </Container>
    </header>
  );
}
