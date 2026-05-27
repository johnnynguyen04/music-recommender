// typed fetch wrappers for the FastAPI inference server.
// dev: http://localhost:8000   prod: NEXT_PUBLIC_API_URL

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ModelName = "neural" | "hybrid";

export interface TrackHit {
  track_id: string;
  artist_name: string;
  track_name: string;
  album_name?: string;
  art_url: string | null;
  preview_url?: string | null;
}

export interface Recommendation {
  track_id: string;
  track_name?: string;
  artist_name?: string;
  album_name?: string;
  camelot?: string | null;
  tempo?: number | null;
  energy?: number | null;
  coherence?: number | null;
  art_url?: string | null;
  preview_url?: string | null;
}

export interface PlaylistPreview {
  playlist_id: string;
  preview: { artist?: string; title?: string }[];
}

export interface MetricsBlob {
  classical?: Record<string, number>;
  neural?: Record<string, number | number[]>;
  hybrid?: Record<string, number | Record<string, number>>;
  comparison?: {
    eval_playlists: number;
    classical: Record<string, number>;
    neural: Record<string, number>;
    hybrid: Record<string, number>;
    alpha: number;
    audio_feature_match_rate: number;
  };
  match_rate?: {
    total_mpd_tracks: number;
    direct_id_matches: number;
    fuzzy_matches: number;
    matched: number;
    match_rate: number;
  };
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => get<{ status: string; loaded: boolean }>("/health"),
  models: () => get<{ available: ModelName[] }>("/models"),
  search: (q: string, limit = 8) =>
    get<{ results: TrackHit[] }>(`/search?q=${encodeURIComponent(q)}&limit=${limit}`),
  samplePlaylists: (n = 25) =>
    get<{ playlists: PlaylistPreview[] }>(`/playlists/sample?n=${n}`),
  playlistTracks: (pid: string, n = 5) =>
    get<{ tracks: TrackHit[] }>(`/playlists/${encodeURIComponent(pid)}/tracks?n=${n}`),
  recommend: (body: {
    playlist_id: string;
    recent_track_ids?: string[];
    seen_track_ids?: string[];
    model?: ModelName;
    k?: number;
  }) =>
    post<{ model: ModelName; playlist_id: string; recommendations: Recommendation[] }>(
      "/recommend",
      body,
    ),
  metrics: () => get<MetricsBlob>("/metrics"),
};
