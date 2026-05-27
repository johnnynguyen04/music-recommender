"use client";

// Single global <audio> element + context so only one preview plays at a
// time, regardless of which card the user clicks. Stores enough track
// metadata that a persistent bottom NowPlayingBar can render from context
// without re-querying the API.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { resetAuroraTint } from "./auroraTint";

export interface TrackInfo {
  id: string;
  title?: string;
  artist?: string;
  art_url?: string | null;
  preview_url?: string | null;
}

interface AudioState {
  current: TrackInfo | null;
  isPlaying: boolean;
  isLoading: boolean;
  progress: number; // 0..1
}

interface AudioCtx extends AudioState {
  toggle: (track: TrackInfo) => void;
  stop: () => void;
  seek: (progress: number) => void;
}

const Ctx = createContext<AudioCtx | null>(null);

export function AudioProvider({ children }: { children: ReactNode }) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [state, setState] = useState<AudioState>({
    current: null,
    isPlaying: false,
    isLoading: false,
    progress: 0,
  });

  const toggle = useCallback(
    (track: TrackInfo) => {
      const el = audioRef.current;
      if (!el || !track.preview_url) return;

      if (state.current?.id === track.id) {
        if (state.isPlaying) {
          el.pause();
          setState((s) => ({ ...s, isPlaying: false }));
        } else {
          void el.play().then(() => setState((s) => ({ ...s, isPlaying: true })));
        }
        return;
      }

      el.pause();
      setState({ current: track, isPlaying: false, isLoading: true, progress: 0 });
      el.src = track.preview_url;
      el.currentTime = 0;
      el.play()
        .then(() =>
          setState({ current: track, isPlaying: true, isLoading: false, progress: 0 }),
        )
        .catch(() =>
          setState({ current: null, isPlaying: false, isLoading: false, progress: 0 }),
        );
    },
    [state.current, state.isPlaying],
  );

  const stop = useCallback(() => {
    audioRef.current?.pause();
    setState({ current: null, isPlaying: false, isLoading: false, progress: 0 });
  }, []);

  const seek = useCallback((progress: number) => {
    const el = audioRef.current;
    if (!el || !Number.isFinite(el.duration)) return;
    el.currentTime = Math.max(0, Math.min(1, progress)) * el.duration;
  }, []);

  // reset aurora to spotify-green whenever the active track clears
  const prevId = useRef<string | null>(null);
  useEffect(() => {
    const id = state.current?.id ?? null;
    if (prevId.current !== null && id === null) {
      resetAuroraTint();
    }
    prevId.current = id;
  }, [state.current]);

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    const onEnded = () =>
      setState({ current: null, isPlaying: false, isLoading: false, progress: 0 });
    el.addEventListener("ended", onEnded);
    return () => el.removeEventListener("ended", onEnded);
  }, []);

  // 60fps progress via RAF so the scrub bar moves smoothly. Only runs while
  // audio is actually playing, so it's free when idle.
  useEffect(() => {
    if (!state.isPlaying) return;
    let raf = 0;
    const tick = () => {
      const el = audioRef.current;
      if (el && Number.isFinite(el.duration) && el.duration > 0) {
        setState((s) => ({ ...s, progress: el.currentTime / el.duration }));
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [state.isPlaying]);

  return (
    <Ctx.Provider value={{ ...state, toggle, stop, seek }}>
      {children}
      {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
      <audio ref={audioRef} preload="none" />
    </Ctx.Provider>
  );
}

export function useAudio() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAudio must be used inside <AudioProvider>");
  return ctx;
}
