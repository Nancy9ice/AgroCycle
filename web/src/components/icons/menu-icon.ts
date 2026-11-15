import { createElement } from "react";
import { Icon, type IconProps } from "./icon";

export function MenuIcon(props: IconProps) {
  return createElement(
    Icon,
    { viewBox: "0 0 24 24", ...props },
    createElement("path", { d: "M4 7h16M4 12h16M4 17h16" }),
  );
}
