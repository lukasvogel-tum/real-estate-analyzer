"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Blocks, Building2, CircleDot, FolderKanban } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type AppShellProps = {
  children: ReactNode;
};

const navItems = [
  {
    href: "/brain",
    label: "Brain",
    description: "Global chat across all knowledge layers",
    icon: Blocks,
  },
  {
    href: "/projects",
    label: "Projects",
    description: "Bestand and geplant workspaces",
    icon: FolderKanban,
  },
];

function getPageContext(pathname: string) {
  if (pathname.startsWith("/brain") || pathname.startsWith("/workspace")) {
    return {
      title: "Brain",
      subtitle: "One global chat across retrieval, metadata, and graph knowledge.",
    };
  }
  if (pathname.startsWith("/projects/")) {
    return {
      title: "Project Detail",
      subtitle: "Focused real-estate analysis workspace for a single project.",
    };
  }
  return {
    title: "Projects",
    subtitle: "Browse deal workspaces, upload files, and open project-specific analysis chats.",
  };
}

export default function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const context = getPageContext(pathname);

  return (
    <div className="min-h-screen bg-[radial-gradient(130%_130%_at_15%_0%,hsl(var(--surface-soft))_0%,hsl(var(--background))_48%,hsl(var(--surface-tint))_100%)]">
      <div className="mx-auto flex w-full max-w-[1440px] gap-4 p-4 md:gap-6 md:p-6">
        <aside className="sticky top-6 hidden h-[calc(100vh-3rem)] w-72 shrink-0 flex-col justify-between rounded-xl border border-border/70 bg-card/88 p-5 shadow-soft backdrop-blur lg:flex">
          <div className="space-y-8">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-3 py-1">
                <Building2 className="h-4 w-4 text-primary" aria-hidden="true" />
                <span className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
                  Family Office Brain
                </span>
              </div>
              <p className="text-sm leading-6 text-muted-foreground">
                Real estate intelligence cockpit for structured uploads and RAG decisions.
              </p>
            </div>

            <nav className="space-y-1" aria-label="Main navigation">
              {navItems.map((item) => {
                const active =
                  pathname === item.href ||
                  (item.href === "/projects" && pathname.startsWith("/projects/")) ||
                  (item.href === "/brain" &&
                    (pathname.startsWith("/brain") || pathname.startsWith("/workspace")));
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "group flex items-start gap-3 rounded-xl border px-3 py-3 transition-colors",
                      active
                        ? "border-primary/15 bg-primary-soft text-foreground"
                        : "border-transparent hover:border-border hover:bg-muted/60",
                    )}
                  >
                    <item.icon
                      className={cn(
                        "mt-0.5 h-4 w-4",
                        active ? "text-primary" : "text-muted-foreground",
                      )}
                      aria-hidden="true"
                    />
                    <span className="space-y-1">
                      <span className="block text-sm font-medium">{item.label}</span>
                      <span className="block text-xs leading-5 text-muted-foreground group-hover:text-foreground/80">
                        {item.description}
                      </span>
                    </span>
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="rounded-lg border border-border/70 bg-background/80 px-3 py-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground">Environment</span>
              <Badge variant="success">MVP Local</Badge>
            </div>
          </div>
        </aside>

        <div className="flex min-h-[calc(100vh-3rem)] flex-1 flex-col gap-4">
          <header className="sticky top-4 z-20 rounded-xl border border-border/70 bg-card/94 px-4 py-3 shadow-soft backdrop-blur md:px-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="space-y-1">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
                  {context.title}
                </p>
                <p className="text-sm leading-6 text-muted-foreground">{context.subtitle}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="gap-1">
                  <CircleDot className="h-3 w-3 text-primary" aria-hidden="true" />
                  Backend expected at :8000
                </Badge>
              </div>
            </div>
            <nav className="mt-3 flex gap-2 overflow-x-auto pb-1 lg:hidden">
              {navItems.map((item) => {
                const active =
                  pathname === item.href ||
                  (item.href === "/projects" && pathname.startsWith("/projects/")) ||
                  (item.href === "/brain" &&
                    (pathname.startsWith("/brain") || pathname.startsWith("/workspace")));
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "inline-flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm font-medium whitespace-nowrap",
                      active
                        ? "border-primary/15 bg-primary-soft text-primary"
                        : "border-border bg-background text-foreground",
                    )}
                  >
                    <item.icon className="h-4 w-4" aria-hidden="true" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </header>

          <main className="flex-1 rounded-xl border border-border/70 bg-card/82 p-4 shadow-soft md:p-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
