"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Search, X, Sparkles, AlertCircle } from "lucide-react";
import GlassCard from "@/components/GlassCard";
import ArtWithPlay from "@/components/ArtWithPlay";
import { api, type ModelName, type Recommendation, type TrackHit, type PlaylistPreview } from "@/lib/api";
import { cn } from "@/lib/utils";
import { item, list } from "@/lib/motion";

type Mode = "search" | "sample";

export default function TryIt() {
  const [mode, setMode] = useState<Mode>("search");
  const [model, setModel] = useState<ModelName>("hybrid");
  const [k, setK] = useState<number>(12);
  const [seeds, setSeeds] = useState<TrackHit[]>([]);
  const [pid, setPid] = useState<string>("");
  const [recs, setRecs] = useState<Recommendation[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = useCallback(async () => {
    setLoading(true); setErr(null);
    try {
      const recent = seeds.map((s) => s.track_id);
      const playlistId = mode === "sample" && pid ? pid : `cold-${recent[0] ?? "x"}`;
      const r = await api.recommend({
        playlist_id: playlistId,
        recent_track_ids: recent,
        model,
        k,
      });
      setRecs(r.recommendations);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [seeds, pid, mode, model, k]);

  const canRun = (mode === "sample" && pid) || (mode !== "sample" && seeds.length > 0);

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-2">
        <h1 className="text-4xl font-bold leading-none tracking-tight md:text-5xl">
          Recommend a song.
        </h1>
        <p className="max-w-[60ch] text-(color:--color-fg-muted) leading-relaxed">
          Pick a few starting songs, choose a model, and see what fits next. The
          model only knows tracks from the Million Playlist Dataset (Spotify, 2010-2017),
          so newer songs won&apos;t show up in search.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1.4fr_1fr]">
        <GlassCard className="p-6 md:p-7">
          <SectionLabel>Songs to start with</SectionLabel>
          <ModeSwitcher mode={mode} onChange={setMode} />
          <div className="mt-5">
            {mode === "search" && (
              <SearchPanel onAdd={(t) => addSeed(seeds, t, setSeeds)} />
            )}
            {mode === "sample" && (
              <SamplePanel pid={pid} setPid={setPid} />
            )}
          </div>
          {mode !== "sample" && (
            <SeedList seeds={seeds} onRemove={(id) => setSeeds((s) => s.filter((x) => x.track_id !== id))} onClear={() => setSeeds([])} />
          )}
        </GlassCard>

        <GlassCard className="p-6 md:p-7">
          <SectionLabel>Options</SectionLabel>
          <div className="mt-4 flex flex-col gap-1.5">
            <span className="text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-(color:--color-fg-dim)">
              How it picks
            </span>
            <Segmented<ModelName>
              options={[
                { value: "hybrid", label: "Music-aware" },
                { value: "neural", label: "Pattern only" },
              ]}
              value={model}
              onChange={setModel}
            />
            <p className="mt-2 text-sm text-(color:--color-fg-muted) leading-relaxed">
              {model === "hybrid"
                ? "Finds songs other people group with yours, then keeps the ones that actually sound right next to your picks — same key feel, close tempo, matching energy."
                : "Finds songs other people group with yours. No check on how they sound together."}
            </p>
          </div>

          <div className="mt-6 flex flex-col gap-2">
            <div className="flex items-baseline justify-between">
              <span className="text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-(color:--color-fg-dim)">
                How many
              </span>
              <span className="num text-lg font-semibold text-(color:--color-accent)">{k}</span>
            </div>
            <input
              type="range"
              min={5}
              max={25}
              step={1}
              value={k}
              onChange={(e) => setK(parseInt(e.target.value, 10))}
              className="accent-(color:--color-accent) w-full"
              aria-label="Number of recommendations"
            />
            <div className="num flex justify-between text-[0.7rem] text-(color:--color-fg-dim)">
              <span>5</span><span>25</span>
            </div>
          </div>

          <button
            disabled={!canRun || loading}
            onClick={run}
            className={cn(
              "mt-6 flex w-full items-center justify-center gap-2 rounded-full py-3 text-sm font-semibold",
              "transition-all duration-150 active:scale-[0.985]",
              canRun && !loading
                ? "bg-(color:--color-accent) text-black hover:bg-(color:--color-accent-hover)"
                : "bg-white/[0.05] text-(color:--color-fg-dim) cursor-not-allowed",
            )}
          >
            <Sparkles size={16} strokeWidth={2} />
            {loading ? "Thinking..." : "Recommend"}
          </button>
          {err && (
            <p className="mt-3 flex items-center gap-2 text-xs text-(color:--color-danger)">
              <AlertCircle size={14} /> {err}
            </p>
          )}
        </GlassCard>
      </div>

      <Results recs={recs} loading={loading} />
    </div>
  );
}

function addSeed(curr: TrackHit[], t: TrackHit, set: (n: TrackHit[]) => void) {
  if (curr.some((s) => s.track_id === t.track_id)) return;
  set([...curr, t]);
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-[0.78rem] font-semibold uppercase tracking-[0.18em] text-(color:--color-fg-muted)">
      {children}
    </h2>
  );
}

function ModeSwitcher({ mode, onChange }: { mode: Mode; onChange: (m: Mode) => void }) {
  const opts: { value: Mode; label: string }[] = [
    { value: "search", label: "Search for songs" },
    { value: "sample", label: "Pick a sample playlist" },
  ];
  return (
    <div className="mt-4 grid grid-cols-2 gap-1 rounded-full bg-black/40 p-1">
      {opts.map((o) => (
        <button
          key={o.value}
          onClick={() => onChange(o.value)}
          className={cn(
            "rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
            mode === o.value
              ? "bg-white/[0.07] text-(color:--color-fg)"
              : "text-(color:--color-fg-muted) hover:text-(color:--color-fg)",
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function Segmented<T extends string>({
  options, value, onChange,
}: { options: { value: T; label: string }[]; value: T; onChange: (v: T) => void }) {
  return (
    <div className="grid grid-cols-2 gap-1 rounded-full bg-black/40 p-1">
      {options.map((o) => (
        <button
          key={o.value}
          onClick={() => onChange(o.value)}
          className={cn(
            "rounded-full px-3 py-2 text-xs font-medium transition-colors",
            value === o.value
              ? "bg-(color:--color-accent)/15 text-(color:--color-accent)"
              : "text-(color:--color-fg-muted) hover:text-(color:--color-fg)",
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function SearchPanel({ onAdd }: { onAdd: (t: TrackHit) => void }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<TrackHit[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!q.trim()) { setHits([]); return; }
    const id = setTimeout(async () => {
      setBusy(true);
      try { const r = await api.search(q, 20); setHits(r.results); } catch { setHits([]); }
      finally { setBusy(false); }
    }, 220);
    return () => clearTimeout(id);
  }, [q]);

  return (
    <div className="flex flex-col gap-3">
      <div className="relative">
        <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-(color:--color-fg-dim)" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Drake, Adele, Bruno Mars, Taylor Swift..."
          className="w-full rounded-full border border-white/[0.08] bg-black/40 py-2.5 pl-10 pr-3 text-sm text-(color:--color-fg) placeholder:text-(color:--color-fg-dim) outline-none focus:border-(color:--color-accent)/40"
        />
      </div>
      {busy && <p className="text-xs text-(color:--color-fg-dim)">Searching...</p>}
      <AnimatePresence mode="popLayout">
        {hits.length > 0 && (
          <motion.ul
            variants={list}
            initial="initial"
            animate="animate"
            exit="initial"
            className="no-scrollbar flex max-h-[320px] flex-col gap-1.5 overflow-y-auto pr-1"
          >
            {hits.map((h) => (
              <motion.li
                key={h.track_id}
                variants={item}
                layout
                className="group flex items-center gap-3 rounded-xl border border-transparent px-2 py-1.5 hover:border-white/[0.05] hover:bg-black/30"
              >
                <ArtWithPlay
                  trackId={h.track_id}
                  art={h.art_url}
                  previewUrl={h.preview_url}
                  title={h.track_name}
                  artist={h.artist_name}
                  alt={h.album_name ?? ""}
                  size={40}
                />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{h.track_name}</div>
                  <div className="truncate text-xs text-(color:--color-fg-muted)">{h.artist_name}</div>
                </div>
                <button
                  onClick={() => { onAdd(h); }}
                  className="rounded-full bg-white/[0.06] px-3 py-1 text-xs font-medium text-(color:--color-fg-muted) opacity-0 transition-all hover:bg-(color:--color-accent) hover:text-black group-hover:opacity-100"
                >
                  Add
                </button>
              </motion.li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}

function SamplePanel({ pid, setPid }: { pid: string; setPid: (s: string) => void }) {
  const [list, setList] = useState<PlaylistPreview[]>([]);
  useEffect(() => { api.samplePlaylists(20).then((r) => setList(r.playlists)).catch(() => {}); }, []);
  return (
    <ul className="no-scrollbar flex max-h-[320px] flex-col gap-1 overflow-y-auto pr-1">
      {list.map((p, idx) => {
        const isActive = p.playlist_id === pid;
        return (
          <li key={p.playlist_id}>
            <button
              onClick={() => setPid(p.playlist_id)}
              className={cn(
                "group flex w-full flex-col items-start gap-0.5 rounded-xl border px-3.5 py-2.5 text-left",
                "transition-all duration-150 active:scale-[0.99]",
                isActive
                  ? "border-(color:--color-accent)/40 bg-(color:--color-accent)/[0.06]"
                  : "border-white/[0.06] bg-black/30 hover:-translate-y-px hover:border-white/[0.14] hover:bg-black/40",
              )}
            >
              <span className="text-sm font-semibold">Sample Playlist #{idx + 1}</span>
              <span className="truncate text-xs text-(color:--color-fg-muted)">
                {p.preview.slice(0, 2).map((t) => `${t.artist} – ${t.title}`).join(" · ")}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

function SeedList({ seeds, onRemove, onClear }: {
  seeds: TrackHit[]; onRemove: (id: string) => void; onClear: () => void;
}) {
  if (seeds.length === 0) {
    return (
      <p className="mt-5 text-xs text-(color:--color-fg-dim)">
        Your starting songs will show up here once you add a few.
      </p>
    );
  }
  return (
    <div className="mt-6">
      <div className="flex items-center justify-between">
        <SectionLabel>Your starting songs</SectionLabel>
        <button onClick={onClear} className="text-xs text-(color:--color-fg-dim) hover:text-(color:--color-fg)">Clear</button>
      </div>
      <motion.ul layout className="mt-3 flex flex-col gap-1.5">
        <AnimatePresence initial={false}>
          {seeds.map((s) => (
            <motion.li
              key={s.track_id}
              layout
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0, transition: { type: "spring", stiffness: 260, damping: 28 } }}
              exit={{ opacity: 0, x: -12, transition: { duration: 0.16 } }}
              className="flex items-center gap-3 rounded-xl border border-white/[0.05] bg-black/30 px-2 py-1.5"
            >
              <ArtWithPlay
                trackId={s.track_id}
                art={s.art_url}
                previewUrl={s.preview_url}
                title={s.track_name}
                artist={s.artist_name}
                alt={s.album_name ?? ""}
                size={40}
              />
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">{s.track_name}</div>
                <div className="truncate text-xs text-(color:--color-fg-muted)">{s.artist_name}</div>
              </div>
              <button onClick={() => onRemove(s.track_id)} className="rounded-full p-1 text-(color:--color-fg-dim) hover:bg-white/[0.06] hover:text-(color:--color-fg)" aria-label="Remove">
                <X size={14} />
              </button>
            </motion.li>
          ))}
        </AnimatePresence>
      </motion.ul>
    </div>
  );
}

function Results({ recs, loading }: { recs: Recommendation[] | null; loading: boolean }) {
  if (loading) {
    return (
      <section className="flex flex-col gap-4">
        <SectionLabel>Suggestions</SectionLabel>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-[88px] animate-pulse rounded-2xl bg-white/[0.04]" />
          ))}
        </div>
      </section>
    );
  }
  if (!recs) return null;
  if (recs.length === 0) {
    return (
      <p className="text-sm text-(color:--color-fg-muted)">
        No suggestions came back. Try adding more starting songs.
      </p>
    );
  }
  return (
    <section className="flex flex-col gap-4">
      <SectionLabel>Suggestions</SectionLabel>
      <motion.ul
        variants={list}
        initial="initial"
        animate="animate"
        className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3"
      >
        {recs.map((r, i) => (
          <motion.li
            key={r.track_id}
            variants={item}
            className="card-hover flex cursor-pointer items-center gap-3 rounded-2xl border border-white/[0.08] bg-black/40 p-3"
          >
            <ArtWithPlay
              trackId={r.track_id}
              art={r.art_url}
              previewUrl={r.preview_url}
              title={r.track_name}
              artist={r.artist_name}
              alt={r.track_name ?? ""}
              size={56}
            />
            <div className="min-w-0 flex-1">
              <div className="num text-[0.7rem] text-(color:--color-fg-dim)">{String(i + 1).padStart(2, "0")}</div>
              <div className="truncate text-sm font-semibold leading-tight">{r.track_name}</div>
              <div className="truncate text-xs text-(color:--color-fg-muted) leading-tight">{r.artist_name}</div>
              <div className="num mt-1 flex items-center gap-2 text-[0.7rem] text-(color:--color-accent)/80">
                {r.camelot && <span>{r.camelot}</span>}
                {r.tempo ? <span>· {Math.round(r.tempo)} BPM</span> : null}
              </div>
            </div>
          </motion.li>
        ))}
      </motion.ul>
    </section>
  );
}

