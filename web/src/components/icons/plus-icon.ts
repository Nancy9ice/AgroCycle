import { createElement } from "react";
import { Icon, type IconProps } from "./icon";

export function PlusIcon(props: IconProps) {
  return createElement(Icon, props, createElement("path", { d: "M10 4v12M4 10h12" }));
}
