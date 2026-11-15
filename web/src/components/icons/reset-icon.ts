import { createElement } from "react";
import { Icon, type IconProps } from "./icon";

export function ResetIcon(props: IconProps) {
  return createElement(
    Icon,
    props,
    createElement("path", { d: "M4 10a6 6 0 1 0 1.8-4.3M4 3.5v3.7h3.7" }),
  );
}
