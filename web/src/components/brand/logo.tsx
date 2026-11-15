import Link from "next/link";
import { LogoMark } from "@/components/icons/logo-mark";
import { routes } from "@/lib/routes";
import { site } from "@/lib/site";
import { cn } from "@/lib/cn";

export { LogoMark } from "@/components/icons/logo-mark";

export function Logo({ className }: { className?: string }) {
  return (
    <Link
      href={routes.home}
      className={cn(
        "inline-flex min-h-11 items-center gap-2.5 font-display text-xl font-semibold",
        className,
      )}
    >
      <LogoMark />
      <span>{site.name}</span>
    </Link>
  );
}
