import { createElement } from "react";
import { Icon, type IconProps } from "./icon";

export function ChevronDownIcon(props: IconProps) {
  return createElement(Icon, props, createElement("path", { d: "M5 8l5 5 5-5" }));
}
