import { createElement } from "react";
import { Icon, type IconProps } from "./icon";

export function LocateIcon(props: IconProps) {
  return createElement(
    Icon,
    props,
    createElement("circle", { cx: "10", cy: "10", r: "3.5" }),
    createElement("path", { d: "M10 2.5V5M10 15v2.5M2.5 10H5M15 10h2.5" }),
  );
}
