import type { Metadata, Viewport } from "next";
import "./globals.css";
import { ToastProvider } from "@/components/Toast";
import ErrorBoundary from "@/components/ErrorBoundary";

export const metadata: Metadata = {
  title: "PathAI - Personalized Learning Path",
  description: "AI-powered education tailored for you. Learn faster with 6 intelligent agents working together for your success.",
  keywords: ["AI learning", "personalized education", "online learning", "SQL tutorial", "adaptive learning"],
  authors: [{ name: "PathAI Team" }],
  openGraph: {
    title: "PathAI - Personalized Learning Path",
    description: "AI-powered education tailored for you",
    type: "website",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
      </head>
      <body className="bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 antialiased">
        <ErrorBoundary>
          <ToastProvider>
            {children}
          </ToastProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
