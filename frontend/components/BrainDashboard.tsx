"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Database,
  FileStack,
  FolderOpen,
  GitBranch,
  RefreshCw,
} from "lucide-react";

import EmptyState from "@/components/app/empty-state";
import LoadingSkeleton from "@/components/app/loading-skeleton";
import PageHeader from "@/components/app/page-header";
import SectionCard from "@/components/app/section-card";
import ScopeChatPanel from "@/components/ScopeChatPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ApiError, fetchKnowledgeStatus } from "@/lib/api";
import type { KnowledgeStatus } from "@/lib/types";

export default function BrainDashboard() {
  const [status, setStatus] = useState<KnowledgeStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadStatus() {
      setError("");
      setIsLoading(true);
      try {
        const result = await fetchKnowledgeStatus();
        if (active) {
          setStatus(result);
        }
      } catch (loadError) {
        if (!active) {
          return;
        }
        if (loadError instanceof ApiError) {
          setError(loadError.detail);
        } else {
          setError("Failed to load system knowledge status.");
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadStatus();

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Brain"
        description="Your single global chat across documents, metadata, and graph knowledge. Use this for broad questions, portfolio context, and cross-domain reasoning."
        actions={
          <>
            <Button asChild variant="outline">
              <Link href="/projects">
                <FolderOpen className="h-4 w-4" aria-hidden="true" />
                Open Projects
              </Link>
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setIsLoading(true);
                setStatus(null);
                setError("");
                void fetchKnowledgeStatus()
                  .then((result) => setStatus(result))
                  .catch((loadError) => {
                    if (loadError instanceof ApiError) {
                      setError(loadError.detail);
                    } else {
                      setError("Failed to load system knowledge status.");
                    }
                  })
                  .finally(() => setIsLoading(false));
              }}
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Refresh Status
            </Button>
          </>
        }
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <ScopeChatPanel
          title="Global Brain Chat"
          subtitle="Uses the global knowledge scope and is designed to become the main entry point for cross-project reasoning."
          defaultScope="global"
          lockScope
          layoutVariant="hero"
          submitLabel="Ask Brain"
          queryPlaceholder="Ask across projects, relationships, documents, risks, or missing information."
        />

        <div className="space-y-4">
          <SectionCard
            title="Knowledge Layers"
            description="Current backend availability across the core data layers."
          >
            {isLoading ? (
              <LoadingSkeleton rows={4} />
            ) : error ? (
              <div className="space-y-3 rounded-md border border-destructive/20 bg-destructive/10 p-4">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            ) : status ? (
              <div className="space-y-3">
                <div className="rounded-lg border border-border bg-background p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <FileStack className="h-4 w-4 text-primary" aria-hidden="true" />
                      <span className="text-sm font-medium">Documents</span>
                    </div>
                    <Badge variant="secondary">
                      {status.metadata.document_count} indexed
                    </Badge>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Projects: {status.projects.count} | Graph-indexed docs:{" "}
                    {status.metadata.graph_indexed_documents}
                  </p>
                </div>

                <div className="rounded-lg border border-border bg-background p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4 text-primary" aria-hidden="true" />
                      <span className="text-sm font-medium">Vector Index</span>
                    </div>
                    <Badge
                      variant={
                        status.vectorstores.global_brain_available ? "success" : "outline"
                      }
                    >
                      {status.vectorstores.global_brain_available ? "available" : "missing"}
                    </Badge>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Global brain:{" "}
                    {status.vectorstores.global_brain_available ? "ready" : "not ready"} |
                    Real-estate shared:{" "}
                    {status.vectorstores.realestate_global_available ? "ready" : "not ready"}
                  </p>
                </div>

                <div className="rounded-lg border border-border bg-background p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <GitBranch className="h-4 w-4 text-primary" aria-hidden="true" />
                      <span className="text-sm font-medium">Neo4j Graph</span>
                    </div>
                    <Badge
                      variant={
                        status.graph.connected
                          ? "success"
                          : status.graph.active
                            ? "warning"
                            : "outline"
                      }
                    >
                      {status.graph.connected
                        ? "connected"
                        : status.graph.active
                          ? "configured"
                          : "inactive"}
                    </Badge>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Nodes: {status.graph.node_count} | Entities: {status.graph.entity_count} |
                    Relations: {status.graph.relationship_count}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    DB: {status.graph.database}
                  </p>
                </div>
              </div>
            ) : (
              <EmptyState
                title="No status available"
                description="The backend did not return a knowledge status payload."
              />
            )}
          </SectionCard>

          <SectionCard
            title="How To Use"
            description="The intended working split between the global brain and project workspaces."
          >
            <div className="space-y-3 text-sm text-muted-foreground">
              <p>
                Use <span className="font-medium text-foreground">Brain</span> for cross-project
                questions, broader relationship reasoning, and later graph-driven family-office
                context.
              </p>
              <p>
                Use <span className="font-medium text-foreground">Projects</span> to open a
                focused real-estate deal workspace with project-specific uploads and a specialized
                analysis chat.
              </p>
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
