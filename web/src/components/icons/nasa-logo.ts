import { createElement } from "react";
import Image from "next/image";
import { cn } from "@/lib/cn";

/** Official insignia; decorative when paired with the adjacent NASA label. */
export function NasaLogo({ className }: { className?: string }) {
  return createElement(Image, {
    src: "/images/nasa-logo.svg",
    alt: "",
    "aria-hidden": true,
    width: 38,
    height: 30,
    loading: "eager",
    className: cn("h-auto w-10 shrink-0", className),
  });
}
