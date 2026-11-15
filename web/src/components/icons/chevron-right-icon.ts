import { createElement } from "react";
import { Icon, type IconProps } from "./icon";

export function ChevronRightIcon(props: IconProps) {
  return createElement(Icon, props, createElement("path", { d: "M8 5l5 5-5 5" }));
}
