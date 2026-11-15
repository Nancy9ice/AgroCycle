import { createElement } from "react";
import { Icon, type IconProps } from "./icon";

export function ArrowRightIcon(props: IconProps) {
  return createElement(
    Icon,
    props,
    createElement("path", { d: "M4 10h12M10 4l6 6-6 6" }),
  );
}
