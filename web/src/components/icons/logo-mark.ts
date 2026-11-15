import { createElement } from "react";
import { cn } from "@/lib/cn";
import type { IconProps } from "./icon";

/** Mark: rotation arcs for the three rotation lengths, around a seed. Decorative. */
export function LogoMark({ className, ...props }: IconProps) {
  return createElement(
    "svg",
    {
      viewBox: "0 0 32 32",
      fill: "none",
      "aria-hidden": true,
      className: cn("size-8 shrink-0", className),
      focusable: "false",
      ...props,
    },
    createElement("path", {
      d: "M16 6a10 10 0 0 1 8.66 5",
      stroke: "#e3b33f",
      strokeWidth: "2.4",
      strokeLinecap: "round",
    }),
    createElement("path", {
      d: "M24.9 16a9 9 0 0 1-4.5 7.8",
      stroke: "#8d7bb8",
      strokeWidth: "2.4",
      strokeLinecap: "round",
    }),
    createElement("path", {
      d: "M16 25a9 9 0 0 1-8-4.9",
      stroke: "#6aa7b9",
      strokeWidth: "2.4",
      strokeLinecap: "round",
    }),
    createElement("path", {
      d: "M7.4 16A8.6 8.6 0 0 1 11 9",
      stroke: "#6f9f58",
      strokeWidth: "2.4",
      strokeLinecap: "round",
    }),
    createElement("circle", {
      cx: "16",
      cy: "16",
      r: "2.6",
      className: "fill-forest-700",
    }),
  );
}
