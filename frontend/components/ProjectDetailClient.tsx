"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiError, fetchProjectInfo } from "@/lib/api";
import type { ProjectInfo } from "@/lib/types";
import ScopeChatPanel from "@/components/ScopeChatPanel";
import UploadForm from "@/components/UploadForm";

type ProjectDetailClientProps = {
  projectName: string;
};

export default function ProjectDetailClient({
  projectName,
}: ProjectDetailClientProps) {
  const [project, setProject] = useState<ProjectInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadProject() {
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
  }

  useEffect(() => {
    void loadProject();
  }, [projectName]);

  return (
    <div className="grid-2">
      <section className="panel">
        <h2 className="panel-title">Project Detail</h2>
        <p className="panel-subtitle">
          Isolated project scope for sensitive due diligence analysis.
        </p>

        <div className="actions" style={{ marginTop: "0.8rem" }}>
          <Link className="button secondary" href="/projects">
            Back to Projects
          </Link>
          <button className="button" type="button" onClick={loadProject}>
            Refresh
          </button>
        </div>

        {isLoading && <p className="muted">Loading project...</p>}
        {error && <p className="status-error">{error}</p>}

        {project && (
          <div style={{ marginTop: "0.9rem" }} className="field-group">
            <div className="tag">{project.project_type}</div>
            <div className="muted">Name: {project.project_name}</div>
            <div className="muted">Files: {project.files_count}</div>
            <div className="muted">Text backups: {project.text_backups_count}</div>
            <div className="muted">Chunks indexed: {project.chunks_indexed}</div>
            <div className="muted">Updated at: {project.updated_at ?? "n/a"}</div>
          </div>
        )}

        <div style={{ marginTop: "1rem" }}>
          <h3 className="panel-title">Add More Documents</h3>
          <p className="panel-subtitle">
            New uploads are indexed in this project, real estate global scope, and global brain scope.
          </p>
          <div style={{ marginTop: "0.7rem" }}>
            <UploadForm
              defaultProjectName={projectName}
              lockProjectScope
              onUploaded={loadProject}
            />
          </div>
        </div>
      </section>

      <ScopeChatPanel
        title="Project Chat"
        subtitle={`Scope locked to project: ${projectName}`}
        defaultScope="project"
        lockedProjectName={projectName}
      />
    </div>
  );
}
