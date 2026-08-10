"use client";

// Single global <audio> element + context. One preview plays at a time.
// Also supports a small queue (Play All on the recommendations).

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { resetArtColor } from "./artColor";

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
  progress: number;
  queueLength: number;
}

interface AudioCtx extends AudioState {
  toggle: (track: TrackInfo) => void;
  stop: () => void;
  seek: (progress: number) => void;
  playQueue: (tracks: TrackInfo[]) => void;
  volume: number;
  setVolume: (v: number) => void;
}

const Ctx = createContext<AudioCtx | null>(null);

export function AudioProvider({ children }: { children: ReactNode }) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const queueRef = useRef<TrackInfo[]>([]);
  const [state, setState] = useState<AudioState>({
    current: null,
    isPlaying: false,
    isLoading: false,
    progress: 0,
    queueLength: 0,
  });

  // play a track directly, bypassing queue-clearing logic
  const startTrack = useCallback((track: TrackInfo) => {
    const el = audioRef.current;
    if (!el || !track.preview_url) return;
    el.pause();
    setState((s) => ({
      ...s, current: track, isPlaying: false, isLoading: true, progress: 0,
    }));
    el.src = track.preview_url;
    el.currentTime = 0;
    el.play()
      .then(() =>
        setState((s) => ({ ...s, current: track, isPlaying: true, isLoading: false })),
      )
      .catch(() => {
        queueRef.current = [];
        setState((s) => ({
          ...s, current: null, isPlaying: false, isLoading: false, queueLength: 0,
        }));
      });
  }, []);

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

      // user clicked a different track manually — clear any active queue
      queueRef.current = [];
      setState((s) => ({ ...s, queueLength: 0 }));
      startTrack(track);
    },
    [state.current, state.isPlaying, startTrack],
  );

  const stop = useCallback(() => {
    queueRef.current = [];
    audioRef.current?.pause();
    setState({
      current: null, isPlaying: false, isLoading: false, progress: 0, queueLength: 0,
    });
  }, []);

  const seek = useCallback((progress: number) => {
    const el = audioRef.current;
    if (!el || !Number.isFinite(el.duration)) return;
    el.currentTime = Math.max(0, Math.min(1, progress)) * el.duration;
  }, []);

  // volume, persisted across visits. iOS ignores element volume; the
  // control is hidden on touch layouts so that's fine.
  const [volume, setVolumeState] = useState(1);
  useEffect(() => {
    const raw = localStorage.getItem("preview-volume");
    const saved = raw === null ? NaN : Number(raw);
    if (Number.isFinite(saved)) {
      const v = Math.max(0, Math.min(1, saved));
      setVolumeState(v);
      if (audioRef.current) audioRef.current.volume = v;
    }
  }, []);
  const setVolume = useCallback((v: number) => {
    const clamped = Math.max(0, Math.min(1, v));
    if (audioRef.current) audioRef.current.volume = clamped;
    setVolumeState(clamped);
    try { localStorage.setItem("preview-volume", String(clamped)); } catch {}
  }, []);

  const playQueue = useCallback(
    (tracks: TrackInfo[]) => {
      const playable = tracks.filter((t) => t.preview_url);
      if (playable.length === 0) return;
      queueRef.current = playable.slice(1);
      setState((s) => ({ ...s, queueLength: queueRef.current.length }));
      startTrack(playable[0]);
    },
    [startTrack],
  );

  // settle the art color back to spotify green when the active track clears
  const prevId = useRef<string | null>(null);
  useEffect(() => {
    const id = state.current?.id ?? null;
    if (prevId.current !== null && id === null) {
      resetArtColor();
    }
    prevId.current = id;
  }, [state.current]);

  // when the current preview ends, advance to next in queue (if any)
  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    const onEnded = () => {
      const next = queueRef.current.shift();
      if (next) {
        setState((s) => ({ ...s, queueLength: queueRef.current.length }));
        startTrack(next);
      } else {
        setState({
          current: null, isPlaying: false, isLoading: false, progress: 0, queueLength: 0,
        });
      }
    };
    el.addEventListener("ended", onEnded);
    return () => el.removeEventListener("ended", onEnded);
  }, [startTrack]);

  // 60fps progress via RAF for smooth scrub bar movement
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
    <Ctx.Provider value={{ ...state, toggle, stop, seek, playQueue, volume, setVolume }}>
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
