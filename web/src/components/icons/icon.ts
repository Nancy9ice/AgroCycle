import { createElement, type SVGProps } from "react";

export type IconProps = SVGProps<SVGSVGElement>;

/** Decorative by default. Give the parent control an accessible name. */
export function Icon(props: IconProps) {
  return createElement("svg", {
    viewBox: "0 0 20 20",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": true,
    focusable: "false",
    ...props,
  });
}
