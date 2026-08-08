"use client";

import { useEffect } from "react";
import { MusicNotes } from "@phosphor-icons/react";
import PlayButton from "./PlayButton";
import { useAudio, type TrackInfo } from "@/lib/audioPlayer";
import { tintAuroraFromArt } from "@/lib/auroraTint";
import { cn } from "@/lib/utils";

interface Props {
  trackId: string;
  art: string | null | undefined;
  previewUrl: string | null | undefined;
  title?: string;
  artist?: string;
  alt?: string;
  size?: number;
  className?: string;
}

// Album art tile with a Spotify-style play button overlay (visible on hover,
// stays visible while this track is the currently playing one).
export default function ArtWithPlay({
  trackId,
  art,
  previewUrl,
  title,
  artist,
  alt,
  size = 52,
  className,
}: Props) {
  const { current } = useAudio();
  const active = current?.id === trackId;
  const buttonSize = Math.max(28, Math.round(size * 0.5));

  // when this track becomes the playing one, tint aurora from its album art
  useEffect(() => {
    if (!active || !art) return;
    void tintAuroraFromArt(art);
  }, [active, art]);

  const track: TrackInfo = {
    id: trackId,
    title,
    artist,
    art_url: art ?? null,
    preview_url: previewUrl ?? null,
  };

  return (
    <div
      style={{ width: size, height: size }}
      className={cn(
        "group/art relative shrink-0 overflow-hidden rounded-lg",
        className,
      )}
    >
      {art ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={art}
          alt={alt ?? ""}
          loading="lazy"
          className="h-full w-full object-cover"
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-white/[0.06] to-white/[0.01]">
          <MusicNotes
            size={Math.round(size * 0.36)}
            className="text-(color:--color-fg-dim)"
          />
        </div>
      )}
      {/* mouse devices: full-overlay play button on hover (or when active) */}
      <div
        className={cn(
          "absolute inset-0 hidden items-center justify-center bg-black/55 transition-opacity duration-150 [@media(hover:hover)]:flex",
          active ? "opacity-100" : "opacity-0 group-hover/art:opacity-100",
        )}
      >
        <PlayButton track={track} size={buttonSize} />
      </div>
      {/* touch devices: small play badge in bottom-right, always visible */}
      <div className="absolute bottom-1 right-1 [@media(hover:hover)]:hidden">
        <PlayButton track={track} size={Math.max(24, Math.round(size * 0.42))} />
      </div>
    </div>
  );
}
