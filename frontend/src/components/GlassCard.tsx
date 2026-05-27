import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}

// Liquid glass card. The .liquid-lens span underneath the content uses
// backdrop-filter with the global SVG displacement filter to bend light
// from whatever's behind it (aurora, other content). Content sits on z-10
// above the lens so it stays crisp.
export default function GlassCard({
  className,
  hover = false,
  children,
  ...rest
}: GlassCardProps) {
  return (
    <div
      className={cn(
        "relative isolate overflow-hidden rounded-3xl",
        hover && "card-hover",
        className,
      )}
      {...rest}
    >
      <span
        aria-hidden="true"
        className="liquid-lens pointer-events-none absolute inset-0 rounded-[inherit]"
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
