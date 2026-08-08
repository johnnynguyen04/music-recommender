"use client";

import { useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { MusicNotes, X } from "@phosphor-icons/react";
import { useAudio } from "@/lib/audioPlayer";
import PlayButton from "./PlayButton";
import { cn } from "@/lib/utils";

// Persistent now-playing bar fixed at the bottom of the viewport.
// Slides up when audio starts, slides back down when it stops.
// Click the scrub bar to seek anywhere in the 30s preview.

export default function NowPlayingBar() {
  const { current, progress, seek, stop, isPlaying } = useAudio();
  const scrubRef = useRef<HTMLDivElement | null>(null);

  return (
    <AnimatePresence>
      {current && (
        <motion.div
          key="npb"
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          transition={{ type: "spring", stiffness: 320, damping: 30 }}
          className="pointer-events-auto fixed inset-x-0 bottom-3 z-30 mx-auto w-[min(640px,calc(100%-1.5rem))] px-3"
        >
          <div
            className={cn(
              "relative isolate overflow-hidden rounded-2xl",
              "border border-white/[0.10]",
              "shadow-[0_24px_60px_-20px_rgba(0,0,0,0.65),inset_0_1px_0_rgba(255,255,255,0.08)]",
            )}
          >
            {/* glass lens layer (same effect as cards) */}
            <span
              aria-hidden="true"
              className="liquid-lens pointer-events-none absolute inset-0 rounded-[inherit]"
            />

            <div className="relative z-10 flex items-center gap-3 px-3 py-2.5">
              {current.art_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={current.art_url}
                  alt=""
                  className="h-12 w-12 shrink-0 rounded-md object-cover"
                />
              ) : (
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-white/[0.05]">
                  <MusicNotes size={18} className="text-(color:--color-fg-dim)" />
                </div>
              )}

              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span aria-hidden="true" className={cn("eq shrink-0", !isPlaying && "paused")}>
                    <i /><i /><i />
                  </span>
                  <span className="truncate text-sm font-semibold leading-tight">
                    {current.title ?? "Unknown track"}
                  </span>
                </div>
                <div className="truncate text-xs text-(color:--color-fg-muted) leading-tight">
                  {current.artist ?? ""}
                </div>
                <ScrubBar
                  ref={scrubRef}
                  progress={progress}
                  isPlaying={isPlaying}
                  onSeek={seek}
                />
              </div>

              <PlayButton track={current} size={36} stopPropagation={false} />

              <button
                onClick={stop}
                aria-label="Close player"
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-(color:--color-fg-dim) transition-colors hover:bg-white/[0.06] hover:text-(color:--color-fg)"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

interface ScrubBarProps {
  progress: number;
  isPlaying: boolean;
  onSeek: (p: number) => void;
}

const ScrubBar = ({ ref, ...props }: ScrubBarProps & { ref?: React.RefObject<HTMLDivElement | null> }) => {
  return (
    <div
      ref={ref}
      role="slider"
      aria-label="Seek preview"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(props.progress * 100)}
      tabIndex={0}
      onClick={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const p = (e.clientX - rect.left) / rect.width;
        props.onSeek(Math.max(0, Math.min(1, p)));
      }}
      className="group/scrub mt-1.5 h-1 cursor-pointer rounded-full bg-white/[0.08]"
    >
      <div
        className="relative h-full rounded-full bg-(color:--color-accent)"
        style={{ width: `${(props.progress * 100).toFixed(2)}%` }}
      >
        <span
          aria-hidden="true"
          className="absolute -right-1.5 top-1/2 h-3 w-3 -translate-y-1/2 rounded-full bg-white opacity-0 shadow-[0_1px_4px_rgba(0,0,0,0.5)] transition-opacity duration-150 group-hover/scrub:opacity-100"
        />
      </div>
    </div>
  );
};
