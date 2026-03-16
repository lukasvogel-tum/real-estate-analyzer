import type { Metadata } from "next";
import type { ReactNode } from "react";

import AppShell from "@/components/app/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Family Office Brain",
  description: "Professional real estate intelligence cockpit",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-background font-sans text-foreground antialiased">
        <div className="min-h-screen">
          <AppShell>{children}</AppShell>
        </div>
      </body>
    </html>
  );
}
