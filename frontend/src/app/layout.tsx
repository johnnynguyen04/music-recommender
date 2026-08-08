import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import LiquidGlassFilter from "@/components/LiquidGlassFilter";
import { AudioProvider } from "@/lib/audioPlayer";
import "./globals.css";

// Geist reads close to SF Pro, which is most of the Apple feel; the mono
// cut keeps metric tables and camelot codes in the same voice.
const geist = Geist({
  variable: "--font-geist",
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
      "Three models compared on the same Spotify playlists, with album-art-reactive aurora and 30-second previews.",
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
    <html lang="en" className={`${geist.variable} ${geistMono.variable}`}>
      <body className="min-h-[100dvh]">
        <LiquidGlassFilter />
        <AudioProvider>{children}</AudioProvider>
        <div className="grain" aria-hidden="true" />
      </body>
    </html>
  );
}
