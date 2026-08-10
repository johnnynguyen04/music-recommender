import type { Metadata } from "next";
import { Figtree, Geist_Mono } from "next/font/google";
import LiquidGlassFilter from "@/components/LiquidGlassFilter";
import { AudioProvider } from "@/lib/audioPlayer";
import "./globals.css";

// Figtree is the closest free cut to Spotify's Circular; Geist Mono stays
// for metric tables and camelot codes.
const figtree = Figtree({
  variable: "--font-figtree",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://music-recommender.vercel.app"),
  title: "Music Recommender",
  description:
    "Three models compared on the same Spotify playlists: classical matrix math, a neural two-tower, and a music-theory-aware hybrid. Hear 30-second previews of every recommendation.",
  openGraph: {
    title: "Music Recommender",
    description:
      "Three models compared on the same Spotify playlists, with 30-second previews of every recommendation.",
    type: "website",
    siteName: "Music Recommender",
  },
  twitter: {
    card: "summary_large_image",
    title: "Music Recommender",
    description:
      "Three models compared on the same Spotify playlists. Hear every recommendation.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${figtree.variable} ${geistMono.variable}`}>
      <body className="min-h-[100dvh]">
        <LiquidGlassFilter />
        <AudioProvider>{children}</AudioProvider>
        <div className="grain" aria-hidden="true" />
      </body>
    </html>
  );
}
