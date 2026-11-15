import { createElement } from "react";
import type { IconProps } from "./icon";

/** Two strokes keep the drawing target visible over light and dark imagery. */
export function MapCrosshairIcon(props: IconProps) {
  return createElement(
    "svg",
    { "aria-hidden": true, focusable: "false", viewBox: "0 0 40 40", ...props },
    createElement(
      "g",
      { stroke: "#0e2616", strokeWidth: "4.5", strokeLinecap: "round" },
      createElement("path", { d: "M20 4v10M20 26v10M4 20h10M26 20h10" }),
    ),
    createElement(
      "g",
      { stroke: "#ffffff", strokeWidth: "2", strokeLinecap: "round" },
      createElement("path", { d: "M20 4v10M20 26v10M4 20h10M26 20h10" }),
    ),
  );
}
