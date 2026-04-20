/**
 * Root Layout
 * Next.js App Router root layout
 */

import type { Metadata } from "next";
import { AppProvider } from "@/lib/app-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "VLM Gateway UI",
  description: "Vision Language Model Gateway User Interface",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body className="bg-base-bg text-text-high antialiased">
        <AppProvider>{children}</AppProvider>
      </body>
    </html>
  );
}
