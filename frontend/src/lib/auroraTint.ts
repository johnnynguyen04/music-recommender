// Album-art-reactive aurora. When a track is playing, pulls a primary +
// secondary color out of its album art and builds the five aurora gradient
// stops from those plus brightness variants. Closer to Apple Music's
// Now-Playing screen: you're inside the song, brand identity steps aside.
// When the audio stops, resetAuroraTint() puts the spotify-green palette back.

interface RGB { r: number; g: number; b: number }

// default green palette, kept in sync with globals.css fallbacks
const BASE = {
  "--aurora-1": { r: 30, g: 215, b: 96 },
  "--aurora-2": { r: 74, g: 222, b: 128 },
  "--aurora-3": { r: 34, g: 197, b: 94 },
  "--aurora-4": { r: 134, g: 239, b: 172 },
  "--aurora-5": { r: 20, g: 83, b: 45 },
};

const memo = new Map<string, { primary: RGB; secondary: RGB } | null>();

export async function tintAuroraFromArt(url: string): Promise<void> {
  if (typeof window === "undefined") return;
  const colors = await dominantPair(url);
  if (!colors) return;
  applyTint(colors.primary, colors.secondary);
}

export function resetAuroraTint(): void {
  if (typeof window === "undefined") return;
  const root = document.documentElement.style;
  for (const [name, c] of Object.entries(BASE)) {
    root.setProperty(name, rgb(c));
  }
}

function applyTint(primary: RGB, secondary: RGB): void {
  const root = document.documentElement.style;
  root.setProperty("--aurora-1", rgb(primary));
  root.setProperty("--aurora-2", rgb(lighten(primary, 0.25)));
  root.setProperty("--aurora-3", rgb(secondary));
  root.setProperty("--aurora-4", rgb(lighten(secondary, 0.32)));
  root.setProperty("--aurora-5", rgb(darken(primary, 0.55)));
}

function rgb(c: RGB): string {
  return `rgb(${Math.round(c.r)}, ${Math.round(c.g)}, ${Math.round(c.b)})`;
}

function lighten(c: RGB, ratio: number): RGB {
  return {
    r: c.r + (255 - c.r) * ratio,
    g: c.g + (255 - c.g) * ratio,
    b: c.b + (255 - c.b) * ratio,
  };
}

function darken(c: RGB, ratio: number): RGB {
  return { r: c.r * (1 - ratio), g: c.g * (1 - ratio), b: c.b * (1 - ratio) };
}

async function dominantPair(url: string) {
  if (memo.has(url)) return memo.get(url)!;
  const result = await sampleImage(url);
  memo.set(url, result);
  return result;
}

function sampleImage(url: string): Promise<{ primary: RGB; secondary: RGB } | null> {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onerror = () => resolve(null);
    img.onload = () => {
      try {
        const SIZE = 40;
        const c = document.createElement("canvas");
        c.width = SIZE;
        c.height = SIZE;
        const ctx = c.getContext("2d");
        if (!ctx) return resolve(null);
        ctx.drawImage(img, 0, 0, SIZE, SIZE);
        const data = ctx.getImageData(0, 0, SIZE, SIZE).data;

        // pass 1: collect saturated pixels and compute weighted-average primary
        const pixels: { rgb: RGB; weight: number }[] = [];
        let r = 0, g = 0, b = 0, w = 0;
        for (let i = 0; i < data.length; i += 4) {
          const pr = data[i], pg = data[i + 1], pb = data[i + 2];
          const max = Math.max(pr, pg, pb);
          const min = Math.min(pr, pg, pb);
          if (max < 30 || max > 245) continue;
          const sat = max === 0 ? 0 : (max - min) / max;
          if (sat < 0.18) continue; // skip near-grayscale
          const weight = sat * sat;
          pixels.push({ rgb: { r: pr, g: pg, b: pb }, weight });
          r += pr * weight;
          g += pg * weight;
          b += pb * weight;
          w += weight;
        }
        if (w < 0.5 || pixels.length === 0) return resolve(null);
        const primary: RGB = { r: r / w, g: g / w, b: b / w };

        // pass 2: secondary = pixel furthest from primary in RGB, weighted by saturation
        let bestScore = -1;
        let secondary: RGB = primary;
        for (const p of pixels) {
          const dr = p.rgb.r - primary.r;
          const dg = p.rgb.g - primary.g;
          const db = p.rgb.b - primary.b;
          const dist = Math.sqrt(dr * dr + dg * dg + db * db);
          const score = dist * p.weight;
          if (score > bestScore) {
            bestScore = score;
            secondary = p.rgb;
          }
        }
        // if secondary is too close to primary, push it toward complementary
        // by mixing in a hue-shifted version (simple R<->B swap with 50% lerp)
        const dr = secondary.r - primary.r;
        const dg = secondary.g - primary.g;
        const db = secondary.b - primary.b;
        if (Math.sqrt(dr * dr + dg * dg + db * db) < 30) {
          secondary = {
            r: 0.5 * primary.b + 0.5 * primary.r,
            g: 0.5 * primary.r + 0.5 * primary.g,
            b: 0.5 * primary.g + 0.5 * primary.b,
          };
        }
        resolve({ primary, secondary });
      } catch {
        resolve(null); // canvas tainted / read failed
      }
    };
    img.src = url;
  });
}
