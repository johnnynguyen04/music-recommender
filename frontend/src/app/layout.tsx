import type { Metadata } from "next";
import { Manrope, JetBrains_Mono } from "next/font/google";
import LiquidGlassFilter from "@/components/LiquidGlassFilter";
import { AudioProvider } from "@/lib/audioPlayer";
import "./globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
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
    <html lang="en" className={`${manrope.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-[100dvh]">
        <LiquidGlassFilter />
        <AudioProvider>{children}</AudioProvider>
      </body>
    </html>
  );
}
