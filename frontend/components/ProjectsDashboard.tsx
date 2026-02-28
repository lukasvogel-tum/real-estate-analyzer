"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiError, fetchProjects } from "@/lib/api";
import type { ProjectInfo } from "@/lib/types";
import UploadForm from "@/components/UploadForm";

export default function ProjectsDashboard() {
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadProjects() {
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

  useEffect(() => {
    void loadProjects();
  }, []);

  return (
    <div className="grid-2">
      <section className="panel">
        <h2 className="panel-title">Project Upload</h2>
        <p className="panel-subtitle">
          Upload and index files directly into project and shared portfolio scope.
        </p>
        <div style={{ marginTop: "0.9rem" }}>
          <UploadForm onUploaded={loadProjects} />
        </div>
      </section>

      <section className="panel">
        <h2 className="panel-title">Projects</h2>
        <p className="panel-subtitle">
          Choose one project for isolated chat, or switch to Workspace for global scopes.
        </p>

        <div className="actions" style={{ marginTop: "0.8rem" }}>
          <button className="button secondary" onClick={loadProjects} type="button">
            Refresh
          </button>
          <Link className="button" href="/workspace">
            Open Workspace
          </Link>
        </div>

        {isLoading && <p className="muted">Loading projects...</p>}
        {error && <p className="status-error">{error}</p>}

        {!isLoading && !error && projects.length === 0 && (
          <p className="muted">No projects yet. Upload a file to create the first project.</p>
        )}

        {!isLoading && !error && projects.length > 0 && (
          <div className="project-grid" style={{ marginTop: "0.9rem" }}>
            {projects.map((project) => (
              <article className="project-card" key={project.project_name}>
                <h3>{project.project_name}</h3>
                <div className="project-meta">
                  <span className="tag">{project.project_type}</span>
                  <span>files {project.files_count}</span>
                  <span>chunks {project.chunks_indexed}</span>
                </div>
                <Link
                  className="button"
                  href={`/projects/${encodeURIComponent(project.project_name)}`}
                >
                  Open Project
                </Link>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
