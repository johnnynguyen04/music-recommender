// Dynamically-rendered OG image for social shares (Twitter, LinkedIn, iMessage).
// Next.js renders this once at build via @vercel/og and serves it as a static PNG.

import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "Music Recommender: three ways to pick the next song";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OGImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "80px",
          background:
            "radial-gradient(ellipse 90% 70% at 80% 10%, rgba(30,215,96,0.32) 0%, transparent 60%), " +
            "radial-gradient(ellipse 70% 50% at 10% 95%, rgba(30,215,96,0.16) 0%, transparent 70%), " +
            "#0a0a0a",
          color: "#ffffff",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            fontSize: 22,
            color: "#1ed760",
            fontWeight: 600,
            letterSpacing: "0.04em",
          }}
        >
          <span>music</span>
          <span style={{ color: "#a3a3a3", fontWeight: 500, letterSpacing: "0.18em" }}>
            / RECOMMENDER
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <div
            style={{
              fontSize: 96,
              fontWeight: 700,
              lineHeight: 1.02,
              letterSpacing: "-0.03em",
            }}
          >
            Recommend a song.
          </div>
          <div
            style={{
              fontSize: 30,
              color: "#d4d4d4",
              lineHeight: 1.35,
              maxWidth: 900,
            }}
          >
            Three models compared on the same Spotify playlists. Classical
            matrix math, a neural two-tower, and a music-theory-aware hybrid.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: 20,
            color: "#a3a3a3",
          }}
        >
          <div style={{ display: "flex", gap: "32px" }}>
            <span>PyTorch</span>
            <span>Next.js</span>
            <span>FastAPI</span>
            <span>AWS S3</span>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              color: "#1ed760",
              fontWeight: 600,
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: "999px",
                background: "#1ed760",
              }}
            />
            github.com/johnnynguyen04/music-recommender
          </div>
        </div>
      </div>
    ),
    { ...size },
  );
}
