import Link from "next/link";
import { routes } from "@/lib/routes";
import { site } from "@/lib/site";
import { cn } from "@/lib/cn";

/** Mark: three arcs for the three rotation lengths, around a seed. Decorative. */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      aria-hidden
      className={cn("size-8 shrink-0", className)}
    >
      <circle cx="16" cy="16" r="16" className="fill-forest-700" />
      <path
        d="M16 6a10 10 0 0 1 8.66 5"
        stroke="#e3b33f"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <path
        d="M24.9 16a9 9 0 0 1-4.5 7.8"
        stroke="#8d7bb8"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <path
        d="M16 25a9 9 0 0 1-8-4.9"
        stroke="#6aa7b9"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <path
        d="M7.4 16A8.6 8.6 0 0 1 11 9"
        stroke="#6f9f58"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <circle cx="16" cy="16" r="2.6" fill="#f7f6f0" />
    </svg>
  );
}

export function Logo({ className }: { className?: string }) {
  return (
    <Link
      href={routes.home}
      className={cn(
        "inline-flex items-center gap-2.5 font-display text-xl font-semibold",
        className,
      )}
    >
      <LogoMark />
      <span>{site.name}</span>
    </Link>
  );
}
