import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { BottomNav } from "@/components/BottomNav";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ToastContainer } from "@/components/Toast";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "The Arbiter - Board Game Rules Q&A",
  description: "Get instant, verified answers to your board game rules questions powered by AI with citation verification.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "The Arbiter",
  },
  keywords: ["board games", "rules", "FAQ", "AI", "arbiter", "game rules"],
  authors: [{ name: "The Arbiter Team" }],
  openGraph: {
    title: "The Arbiter - Board Game Rules Q&A",
    description: "Get instant, verified answers to your board game rules questions",
    type: "website",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#0a0a0a",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} font-sans antialiased min-h-screen bg-background text-foreground`}
      >
        <ErrorBoundary>
          <main className="min-w-[320px] pb-20">
            {children}
          </main>
        </ErrorBoundary>
        <BottomNav />
        <ToastContainer />
      </body>
    </html>
  );
}
