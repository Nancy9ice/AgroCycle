import { createElement } from "react";
import { Icon, type IconProps } from "./icon";

export function UploadIcon(props: IconProps) {
  return createElement(
    Icon,
    props,
    createElement("path", { d: "M10 13V3.5M6.5 7 10 3.5 13.5 7M3.5 13v3h13v-3" }),
  );
}
