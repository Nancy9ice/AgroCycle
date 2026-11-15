import { createElement } from "react";
import { Icon, type IconProps } from "./icon";

export function CheckIcon(props: IconProps) {
  return createElement(Icon, props, createElement("path", { d: "M4 10.5l4 4 8-9" }));
}
