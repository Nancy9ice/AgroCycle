import Link from "next/link";
import type { ComponentProps } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost";

const base =
  "inline-flex min-h-12 items-center justify-center gap-2 rounded-full px-6 text-base font-semibold transition-colors";

const variants: Record<Variant, string> = {
  primary: "bg-forest-700 text-white hover:bg-forest-800 active:bg-forest-950",
  secondary:
    "border border-line-strong bg-surface text-ink hover:border-forest-600 hover:bg-forest-50",
  ghost: "text-forest-700 hover:bg-forest-100",
};

interface ButtonLinkProps extends Omit<ComponentProps<typeof Link>, "className"> {
  variant?: Variant;
  className?: string;
}

/** A link styled as a button. Navigation is always a link, never a click handler. */
export function ButtonLink({
  variant = "primary",
  className,
  ...props
}: ButtonLinkProps) {
  return <Link className={cn(base, variants[variant], className)} {...props} />;
}
