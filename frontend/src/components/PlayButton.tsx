"use client";

import { CircleNotch, Pause, Play } from "@phosphor-icons/react";
import { useAudio, type TrackInfo } from "@/lib/audioPlayer";
import { cn } from "@/lib/utils";

interface PlayButtonProps {
  track: TrackInfo;
  size?: number;
  className?: string;
  /** stop event propagation so clicking play doesn't trigger parent button/card. */
  stopPropagation?: boolean;
}

export default function PlayButton({
  track,
  size = 32,
  className,
  stopPropagation = true,
}: PlayButtonProps) {
  const { current, isPlaying, isLoading, toggle } = useAudio();
  const active = current?.id === track.id;
  const playing = active && isPlaying;
  const loading = active && isLoading;
  const disabled = !track.preview_url;

  const iconSize = Math.round(size * 0.42);

  return (
    <button
      type="button"
      onClick={(e) => {
        if (stopPropagation) e.stopPropagation();
        toggle(track);
      }}
      disabled={disabled}
      aria-label={playing ? "Pause preview" : "Play 30-second preview"}
      title={
        disabled
          ? "No preview available for this track"
          : playing
            ? "Pause"
            : "Play 30s preview"
      }
      style={{ width: size, height: size }}
      className={cn(
        "flex shrink-0 items-center justify-center rounded-full",
        "transition-all duration-150 active:scale-90",
        disabled
          ? "cursor-not-allowed bg-white/[0.04] text-(color:--color-fg-dim) opacity-60"
          : playing
            ? "bg-(color:--color-accent) text-black shadow-[0_4px_16px_-4px_rgba(30,215,96,0.6)] hover:bg-(color:--color-accent-hover)"
            : "bg-white text-black hover:scale-105 hover:bg-(color:--color-accent)",
        className,
      )}
    >
      {loading ? (
        <CircleNotch size={iconSize} className="animate-spin" />
      ) : playing ? (
        <Pause size={iconSize} weight="fill" />
      ) : (
        <Play size={iconSize} weight="fill" className="ml-[1px]" />
      )}
    </button>
  );
}
