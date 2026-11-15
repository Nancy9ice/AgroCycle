import { createElement } from "react";
import { Icon, type IconProps } from "./icon";

export function ArrowLeftIcon(props: IconProps) {
  return createElement(
    Icon,
    props,
    createElement("path", { d: "M16 10H4M10 4l-6 6 6 6" }),
  );
}
