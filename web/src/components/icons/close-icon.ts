import { createElement } from "react";
import { Icon, type IconProps } from "./icon";

export function CloseIcon(props: IconProps) {
  return createElement(
    Icon,
    { viewBox: "0 0 24 24", ...props },
    createElement("path", { d: "M6 6l12 12M18 6L6 18" }),
  );
}
