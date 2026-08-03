"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  Clock3,
  Database,
  FileStack,
  RefreshCw,
  Text,
} from "lucide-react";

import EmptyState from "@/components/app/empty-state";
import LoadingSkeleton from "@/components/app/loading-skeleton";
import PageHeader from "@/components/app/page-header";
import SectionCard from "@/components/app/section-card";
import ScopeChatPanel from "@/components/ScopeChatPanel";
import UploadForm from "@/components/UploadForm";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ApiError, fetchProjectInfo } from "@/lib/api";
import { getProjectTypeLabel, normalizeProjectType } from "@/lib/project-utils";
import type { ProjectInfo } from "@/lib/types";

type ProjectDetailClientProps = {
  projectName: string;
};

type ProjectStatCardProps = {
  label: string;
  value: string | number;
  icon: typeof FileStack;
};

function ProjectStatCard({ label, value, icon: Icon }: ProjectStatCardProps) {
  return (
    <div className="rounded-2xl border border-border bg-card/95 p-4 shadow-soft">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
          {label}
        </p>
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-border bg-background">
          <Icon className="h-4 w-4 text-primary" aria-hidden="true" />
        </div>
      </div>
      <p className="mt-4 text-2xl font-semibold tracking-tight text-foreground">{value}</p>
    </div>
  );
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "n/a";
  }

  return new Date(value).toLocaleString();
}

export default function ProjectDetailClient({
  projectName,
}: ProjectDetailClientProps) {
  const [project, setProject] = useState<ProjectInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadProject = useCallback(async () => {
    setError("");
    setIsLoading(true);
    try {
      const result = await fetchProjectInfo(projectName);
      setProject(result);
    } catch (loadError) {
      if (loadError instanceof ApiError) {
        setError(loadError.detail);
      } else {
        setError("Failed to load project details.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [projectName]);

  useEffect(() => {
    void loadProject();
  }, [loadProject]);

  const normalizedType = normalizeProjectType(project?.project_type ?? "geplant");
  const projectTypeLabel = getProjectTypeLabel(project?.project_type ?? "geplant");

  const stats = useMemo(() => {
    if (!project) {
      return [];
    }

    return [
      {
        label: "Files",
        value: project.files_count,
        icon: FileStack,
      },
      {
        label: "Text Backups",
        value: project.text_backups_count,
        icon: Text,
      },
      {
        label: "Indexed Chunks",
        value: project.chunks_indexed,
        icon: Database,
      },
      {
        label: "Last Updated",
        value: formatDateTime(project.updated_at),
        icon: Clock3,
      },
    ];
  }, [project]);

  return (
    <div className="space-y-6">
      <PageHeader
        title={projectName}
        description="Focused project workspace for asset-specific reasoning, uploads, and later structured underwriting workflows."
        actions={
          <>
            <Button asChild variant="outline">
              <Link href="/projects">
                <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                Back to Projects
              </Link>
            </Button>
            <Button variant="outline" onClick={loadProject}>
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Refresh
            </Button>
          </>
        }
      />

      {error ? (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4">
          <p className="text-sm text-destructive">{error}</p>
          <Button variant="outline" onClick={loadProject} className="mt-3">
            Retry
          </Button>
        </div>
      ) : null}

      {isLoading ? <LoadingSkeleton rows={6} /> : null}

      {!isLoading && !project ? (
        <EmptyState
          title="Project not found"
          description="This workspace could not be loaded from the backend."
        />
      ) : null}

      {project ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((item) => (
              <ProjectStatCard
                key={item.label}
                label={item.label}
                value={item.value}
                icon={item.icon}
              />
            ))}
          </section>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
            <ScopeChatPanel
              title="Project Analysis Chat"
              subtitle={`Scope locked to ${projectName}. Use this workspace for focused real-estate reasoning inside a single deal context.`}
              defaultScope="project"
              lockedProjectName={projectName}
              queryPlaceholder="Ask for investment risks, missing documents, valuation assumptions, rent roll issues, or acquisition questions."
              submitLabel="Analyze Project"
            />

            <div className="space-y-4">
              <SectionCard
                title="Workspace Context"
                description="Operational status and role of this project workspace."
                actions={
                  <Badge variant={normalizedType === "bestand" ? "success" : "warning"}>
                    {projectTypeLabel}
                  </Badge>
                }
                className="border-border/70 bg-card/95"
              >
                <div className="rounded-2xl border border-border bg-background p-4">
                  <p className="text-sm font-medium text-foreground">Retrieval status</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Badge variant={project.has_vector_index ? "success" : "outline"}>
                      {project.has_vector_index ? "vector index ready" : "vector index pending"}
                    </Badge>
                    <Badge variant="outline">table: {project.table_name}</Badge>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-muted-foreground">
                    Uploads in this workspace stay project-scoped and also contribute to shared
                    portfolio and global retrieval.
                  </p>
                </div>

                <div className="rounded-2xl border border-border bg-background p-4">
                  <p className="text-sm font-medium text-foreground">Recommended use</p>
                  <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
                    <li>Ask for missing data, document gaps, and due diligence risks.</li>
                    <li>Use project uploads to keep one clean context per asset or deal.</li>
                    <li>Use Brain only when the question spans multiple projects.</li>
                  </ul>
                </div>
              </SectionCard>

              <SectionCard
                title="Add Documents"
                description="New uploads remain available in this project and the broader shared layers."
                className="border-border/70 bg-card/95"
              >
                <UploadForm
                  defaultProjectName={projectName}
                  lockProjectScope
                  onUploaded={(response) => {
                    setSuccess(`Indexed ${response.chunks_created} chunks for this project.`);
                    void loadProject();
                  }}
                />
                {success ? (
                  <p
                    className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800"
                    aria-live="polite"
                  >
                    {success}
                  </p>
                ) : null}
              </SectionCard>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
