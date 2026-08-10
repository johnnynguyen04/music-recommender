// Extracts the playing track's primary color from its album art and exposes
// it as --art-color on :root. Everything that follows the song (top wash,
// player glow, equalizer, scrub fill, playing-card border) reads that one
// var; the @property transition in globals.css eases every change.
// resetArtColor() puts the spotify green back when playback stops.

interface RGB { r: number; g: number; b: number }

const SPOTIFY_GREEN: RGB = { r: 30, g: 215, b: 96 };

const memo = new Map<string, RGB | null>();

export async function setArtColorFromImage(url: string): Promise<void> {
  if (typeof window === "undefined") return;
  const primary = await dominantColor(url);
  if (!primary) return;
  document.documentElement.style.setProperty("--art-color", rgb(primary));
}

export function resetArtColor(): void {
  if (typeof window === "undefined") return;
  document.documentElement.style.setProperty("--art-color", rgb(SPOTIFY_GREEN));
}

function rgb(c: RGB): string {
  return `rgb(${Math.round(c.r)}, ${Math.round(c.g)}, ${Math.round(c.b)})`;
}

async function dominantColor(url: string): Promise<RGB | null> {
  if (memo.has(url)) return memo.get(url)!;
  const result = await sampleImage(url);
  memo.set(url, result);
  return result;
}

function sampleImage(url: string): Promise<RGB | null> {
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

        // saturation-weighted average of the non-grayscale pixels, so the
        // "loudest" color wins rather than the most common one
        let r = 0, g = 0, b = 0, w = 0;
        for (let i = 0; i < data.length; i += 4) {
          const pr = data[i], pg = data[i + 1], pb = data[i + 2];
          const max = Math.max(pr, pg, pb);
          const min = Math.min(pr, pg, pb);
          if (max < 30 || max > 245) continue;
          const sat = max === 0 ? 0 : (max - min) / max;
          if (sat < 0.18) continue; // skip near-grayscale
          const weight = sat * sat;
          r += pr * weight;
          g += pg * weight;
          b += pb * weight;
          w += weight;
        }
        if (w < 0.5) return resolve(null);
        resolve({ r: r / w, g: g / w, b: b / w });
      } catch {
        resolve(null); // canvas tainted / read failed
      }
    };
    img.src = url;
  });
}
