import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}

// Opaque content surface, Spotify-style: flat #121212-family fill, hairline
// border, small radius. Glass (the .liquid-lens treatment) is reserved for
// floating chrome only — the nav island and the now-playing bar.
export default function GlassCard({
  className,
  hover = false,
  children,
  ...rest
}: GlassCardProps) {
  return (
    <div
      className={cn(
        "relative rounded-xl border border-white/[0.06] bg-(color:--color-surface)",
        "shadow-[0_1px_0_rgba(255,255,255,0.03)_inset,0_8px_24px_-16px_rgba(0,0,0,0.5)]",
        hover && "card-hover",
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
