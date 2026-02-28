import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "Family Office Brain",
  description: "Real Estate intelligence cockpit MVP",
};

const NAV_ITEMS = [
  { href: "/projects", label: "Projects" },
  { href: "/workspace", label: "Workspace" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <header className="topbar">
            <div className="brand">
              <span className="brand-title">Family Office Brain</span>
              <span className="brand-subtitle">
                Real Estate MVP Control Surface
              </span>
            </div>

            <nav className="nav">
              {NAV_ITEMS.map((item) => (
                <Link key={item.href} href={item.href} className="nav-link">
                  {item.label}
                </Link>
              ))}
            </nav>
          </header>

          <main className="page-shell">{children}</main>
        </div>
      </body>
    </html>
  );
}
