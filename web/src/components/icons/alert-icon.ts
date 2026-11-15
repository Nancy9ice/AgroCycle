import { createElement } from "react";
import { Icon, type IconProps } from "./icon";

export function AlertIcon(props: IconProps) {
  return createElement(Icon, props, createElement("path", { d: "M10 5v6M10 14.5v.5" }));
}
