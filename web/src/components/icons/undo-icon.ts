import { createElement } from "react";
import { Icon, type IconProps } from "./icon";

export function UndoIcon(props: IconProps) {
  return createElement(
    Icon,
    props,
    createElement("path", { d: "M4 8h7.5a4.5 4.5 0 0 1 0 9H8M4 8l4-4M4 8l4 4" }),
  );
}
