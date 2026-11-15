import Image from "next/image";
import { cn } from "@/lib/cn";

interface HomePhotoProps {
  src: string;
  alt: string;
  className?: string;
  sizes?: string;
}

/** A rounded photo frame. Pass a `home-photo-*` class to set its shape. */
export function HomePhoto({ src, alt, className, sizes = "100vw" }: HomePhotoProps) {
  return (
    <div className={cn("home-photo", className)}>
      <Image src={src} alt={alt} fill sizes={sizes} />
    </div>
  );
}
