"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  Building2,
  Clock3,
  FolderClosed,
  Home,
  Plus,
  RefreshCw,
  TrendingUp,
} from "lucide-react";

import EmptyState from "@/components/app/empty-state";
import LoadingSkeleton from "@/components/app/loading-skeleton";
import PageHeader from "@/components/app/page-header";
import SectionCard from "@/components/app/section-card";
import UploadForm from "@/components/UploadForm";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ApiError, fetchProjects } from "@/lib/api";
import { getProjectTypeLabel, normalizeProjectType } from "@/lib/project-utils";
import type { ProjectInfo } from "@/lib/types";

function formatDate(value: string | null) {
  if (!value) {
    return "No updates yet";
  }

  return new Date(value).toLocaleDateString();
}

function OverviewCard({
  title,
  value,
  description,
  icon: Icon,
}: {
  title: string;
  value: number;
  description: string;
  icon: typeof Home;
}) {
  return (
    <div className="rounded-2xl border border-border bg-card/90 p-5 shadow-soft">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            {title}
          </p>
          <p className="mt-3 text-3xl font-semibold tracking-tight text-foreground">{value}</p>
        </div>
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-border bg-background">
          <Icon className="h-5 w-5 text-primary" aria-hidden="true" />
        </div>
      </div>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{description}</p>
    </div>
  );
}

function ProjectFolderCard({ project }: { project: ProjectInfo }) {
  const normalizedType = normalizeProjectType(project.project_type);
  const label = getProjectTypeLabel(project.project_type);
  const description =
    normalizedType === "bestand"
      ? "Operational workspace for held assets and active management decisions."
      : "Pipeline workspace for target assets, due diligence, and early evaluation.";

  return (
    <Link
      href={`/projects/${encodeURIComponent(project.project_name)}`}
      className="group block rounded-[24px] border border-border bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(246,249,252,0.92))] p-5 shadow-soft transition duration-200 hover:-translate-y-0.5 hover:border-primary/35"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-[18px] border border-border bg-background">
            {normalizedType === "bestand" ? (
              <Building2 className="h-5 w-5 text-primary" aria-hidden="true" />
            ) : (
              <FolderClosed className="h-5 w-5 text-primary" aria-hidden="true" />
            )}
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-semibold tracking-tight text-foreground">
              {project.project_name}
            </h3>
            <p className="text-sm leading-6 text-muted-foreground">{description}</p>
          </div>
        </div>
        <Badge variant={normalizedType === "bestand" ? "success" : "warning"}>{label}</Badge>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl border border-border bg-background/90 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Files
          </p>
          <p className="mt-2 text-2xl font-semibold text-foreground">{project.files_count}</p>
        </div>
        <div className="rounded-2xl border border-border bg-background/90 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Indexed Chunks
          </p>
          <p className="mt-2 text-2xl font-semibold text-foreground">{project.chunks_indexed}</p>
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between border-t border-border/70 pt-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock3 className="h-4 w-4" aria-hidden="true" />
          Updated {formatDate(project.updated_at)}
        </div>
        <span className="inline-flex items-center gap-2 text-sm font-medium text-primary">
          Open workspace
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </span>
      </div>
    </Link>
  );
}

type FolderSectionProps = {
  title: string;
  description: string;
  icon: typeof Home;
  projects: ProjectInfo[];
  isLoading: boolean;
};

function FolderSection({
  title,
  description,
  icon: Icon,
  projects,
  isLoading,
}: FolderSectionProps) {
  const totalFiles = projects.reduce((sum, project) => sum + project.files_count, 0);
  const totalChunks = projects.reduce((sum, project) => sum + project.chunks_indexed, 0);

  return (
    <SectionCard
      title={title}
      description={description}
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{projects.length} workspaces</Badge>
          <Badge variant="secondary">{totalFiles} files</Badge>
          <Badge variant="secondary">{totalChunks} chunks</Badge>
        </div>
      }
      className="border-border/70 bg-card/95"
      contentClassName="space-y-5"
    >
      {isLoading ? (
        <LoadingSkeleton rows={4} />
      ) : projects.length === 0 ? (
        <EmptyState
          title={`No ${title.toLowerCase()} projects yet`}
          description="Create one by uploading project documents with the matching project type."
          icon={Icon}
        />
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {projects.map((project) => (
            <ProjectFolderCard key={project.project_name} project={project} />
          ))}
        </div>
      )}
    </SectionCard>
  );
}

export default function ProjectsDashboard() {
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let active = true;

    async function loadProjects() {
      setError("");
      setIsLoading(true);
      try {
        const result = await fetchProjects();
        if (active) {
          setProjects(result);
        }
      } catch (loadError) {
        if (!active) {
          return;
        }
        if (loadError instanceof ApiError) {
          setError(loadError.detail);
        } else {
          setError("Failed to load projects.");
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadProjects();

    return () => {
      active = false;
    };
  }, []);

  const bestandProjects = projects.filter(
    (project) => normalizeProjectType(project.project_type) === "bestand",
  );
  const plannedProjects = projects.filter(
    (project) => normalizeProjectType(project.project_type) === "geplant",
  );
  const totalFiles = projects.reduce((sum, project) => sum + project.files_count, 0);
  const totalChunks = projects.reduce((sum, project) => sum + project.chunks_indexed, 0);

  async function refreshProjects() {
    setError("");
    setIsLoading(true);
    try {
      const result = await fetchProjects();
      setProjects(result);
    } catch (loadError) {
      if (loadError instanceof ApiError) {
        setError(loadError.detail);
      } else {
        setError("Failed to load projects.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Projects"
        description="Manage deal workspaces with clear separation between held assets and planned opportunities. Each project keeps a focused chat while still feeding the Brain."
        actions={
          <>
            <Button asChild variant="outline">
              <Link href="/brain">Open Brain</Link>
            </Button>
            <Button variant="outline" onClick={() => void refreshProjects()}>
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Refresh
            </Button>
          </>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <OverviewCard
          title="Workspaces"
          value={projects.length}
          description="All current project workspaces across Bestand and Geplant."
          icon={FolderClosed}
        />
        <OverviewCard
          title="Bestand"
          value={bestandProjects.length}
          description="Operational assets already inside the portfolio."
          icon={Home}
        />
        <OverviewCard
          title="Geplant"
          value={plannedProjects.length}
          description="Pipeline opportunities and active evaluation candidates."
          icon={Building2}
        />
        <OverviewCard
          title="Indexed Chunks"
          value={totalChunks}
          description={`${totalFiles} uploaded files currently contribute to retrieval.`}
          icon={TrendingUp}
        />
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(340px,420px)_1fr]">
        <SectionCard
          title="Create Or Update Workspace"
          description="Upload project documents here. Project uploads stay available in the project chat and are also visible to Brain."
          actions={
            <Badge variant="secondary" className="gap-1">
              <Plus className="h-3.5 w-3.5" aria-hidden="true" />
              Project-first
            </Badge>
          }
          className="border-border/70 bg-card/95"
          contentClassName="space-y-5"
        >
          <div className="rounded-2xl border border-border bg-muted/25 p-4">
            <p className="text-sm font-medium text-foreground">Recommended workflow</p>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              Create one clean workspace per asset or deal. Use `Bestand` for held properties and
              `Geplant` for target deals still under review.
            </p>
          </div>

          <UploadForm
            onUploaded={(response) => {
              setSuccess(
                `Indexed ${response.chunks_created} chunks for ${response.project_name}.`,
              );
              void refreshProjects();
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

        <div className="space-y-4">
          {error ? (
            <div className="space-y-3 rounded-md border border-destructive/20 bg-destructive/10 p-4">
              <p className="text-sm text-destructive">{error}</p>
              <Button variant="outline" onClick={() => void refreshProjects()}>
                Retry
              </Button>
            </div>
          ) : null}

          <FolderSection
            title="Bestand"
            description="Held assets and active operating workspaces."
            icon={Home}
            projects={bestandProjects}
            isLoading={isLoading}
          />

          <FolderSection
            title="Geplant"
            description="Target assets, pipeline deals, and prospective investments."
            icon={FolderClosed}
            projects={plannedProjects}
            isLoading={isLoading}
          />
        </div>
      </div>

      <SectionCard
        title="Workspace Model"
        description="How projects fit into the broader product structure."
        className="border-border/70 bg-card/95"
      >
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-border bg-background p-4">
            <p className="text-sm font-medium text-foreground">Project Chat</p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Focused due diligence, missing-data checks, and asset-specific reasoning.
            </p>
          </div>
          <div className="rounded-2xl border border-border bg-background p-4">
            <p className="text-sm font-medium text-foreground">Shared Retrieval</p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Project uploads also contribute to shared portfolio and global knowledge scopes.
            </p>
          </div>
          <div className="rounded-2xl border border-border bg-background p-4">
            <p className="text-sm font-medium text-foreground">Brain</p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Use Brain for cross-project questions after the workspaces are kept clean.
            </p>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}
