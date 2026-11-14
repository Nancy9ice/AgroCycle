import { routes } from "@/lib/routes";

/** In-page anchors on the home page, shown in the header. */
export const homeNav = [
  { label: "The decision", href: `${routes.home}#decision` },
  { label: "Three options", href: `${routes.home}#strategies` },
  { label: "How it works", href: `${routes.home}#how-it-works` },
  { label: "Honest answers", href: `${routes.home}#honesty` },
  { label: "Evidence", href: `${routes.home}#evidence` },
] as const;
