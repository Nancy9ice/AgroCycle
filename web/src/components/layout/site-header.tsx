import { CloseIcon } from "@/components/icons/close-icon";
import { MenuIcon } from "@/components/icons/menu-icon";
import { Logo } from "@/components/brand/logo";
import { homeNav } from "@/components/layout/nav-links";
import { ScrollHeader } from "@/components/layout/scroll-header";
import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { routes } from "@/lib/routes";

const navLink =
  "rounded-full px-3.5 py-2 text-[0.9375rem] font-medium text-ink-soft underline-offset-8 transition-colors hover:text-forest-800 hover:underline";

export function SiteHeader() {
  return (
    <ScrollHeader className="sticky top-0 z-40 border-b border-line/80 bg-paper/90 backdrop-blur print:hidden">
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
              className="flex size-9 cursor-pointer list-none items-center justify-center rounded-none bg-surface p-1 [&::-webkit-details-marker]:hidden"
              aria-label="Menu"
            >
              <MenuIcon className="size-5 group-open:hidden" />
              <CloseIcon className="hidden size-5 group-open:block" />
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
    </ScrollHeader>
  );
}
