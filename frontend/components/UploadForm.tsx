"use client";

import { FormEvent, useMemo, useState } from "react";

import { ApiError, uploadDocuments } from "@/lib/api";
import type { ProjectType, UploadScopeType } from "@/lib/types";

type UploadFormProps = {
  defaultProjectName?: string;
  lockProjectScope?: boolean;
  onUploaded?: () => void;
};

export default function UploadForm({
  defaultProjectName = "",
  lockProjectScope = false,
  onUploaded,
}: UploadFormProps) {
  const [scopeType, setScopeType] = useState<UploadScopeType>("project");
  const [scopeId, setScopeId] = useState(defaultProjectName);
  const [documentType, setDocumentType] = useState("general");
  const [projectType, setProjectType] = useState<ProjectType>("potenziell");
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");
  const isLockedProject = lockProjectScope && defaultProjectName.trim().length > 0;

  const effectiveScopeType: UploadScopeType = isLockedProject ? "project" : scopeType;

  const fileSummary = useMemo(() => {
    if (files.length === 0) {
      return "No files selected";
    }
    if (files.length <= 3) {
      return files.map((file) => file.name).join(", ");
    }
    return `${files.length} files selected`;
  }, [files]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("");
    setError("");

    if (!scopeId.trim()) {
      setError("Scope ID is required.");
      return;
    }
    if (files.length === 0) {
      setError("Select at least one file.");
      return;
    }

    setIsSubmitting(true);
    try {
      const normalizedScopeId = scopeId.trim();
      const response = await uploadDocuments({
        scopeType: effectiveScopeType,
        scopeId: normalizedScopeId,
        documentType: documentType.trim() || "general",
        projectName: effectiveScopeType === "project" ? normalizedScopeId : undefined,
        projectType: effectiveScopeType === "project" ? projectType : undefined,
        files,
      });
      setStatus(
        `Upload complete: ${response.chunks_created} chunks indexed for ${response.scope_type}:${response.scope_id}.`,
      );
      setFiles([]);
      onUploaded?.();
    } catch (uploadError) {
      if (uploadError instanceof ApiError) {
        setError(uploadError.detail);
      } else if (uploadError instanceof Error) {
        setError(uploadError.message);
      } else {
        setError("Upload failed due to an unknown error.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="field-group">
      <div className="field">
        <label htmlFor="scopeType">Scope Type</label>
        <select
          id="scopeType"
          value={effectiveScopeType}
          disabled={isLockedProject}
          onChange={(event) => setScopeType(event.target.value as UploadScopeType)}
        >
          <option value="project">project</option>
          <option value="domain">domain</option>
          <option value="global">global</option>
        </select>
      </div>

      <div className="field">
        <label htmlFor="scopeId">Scope ID</label>
        <input
          id="scopeId"
          value={scopeId}
          onChange={(event) => setScopeId(event.target.value)}
          placeholder={
            effectiveScopeType === "project"
              ? "e.g. Berlin-Mitte-Deal"
              : effectiveScopeType === "domain"
                ? "e.g. corporate, insurance, tax"
                : "global"
          }
          disabled={isLockedProject}
        />
      </div>

      <div className="field">
        <label htmlFor="documentType">Document Type</label>
        <input
          id="documentType"
          value={documentType}
          onChange={(event) => setDocumentType(event.target.value)}
          placeholder="e.g. expose, bilanz, versicherung, gesellschaftsstruktur"
        />
      </div>

      {effectiveScopeType === "project" && (
        <div className="field">
          <label htmlFor="projectType">Project Type</label>
          <select
            id="projectType"
            value={projectType}
            onChange={(event) => setProjectType(event.target.value as ProjectType)}
          >
            <option value="potenziell">potenziell</option>
            <option value="bestand">bestand</option>
          </select>
        </div>
      )}

      <div className="field">
        <label htmlFor="files">Documents</label>
        <input
          id="files"
          type="file"
          multiple
          onChange={(event) => {
            const selectedFiles = Array.from(event.target.files ?? []);
            setFiles(selectedFiles);
          }}
        />
        <span className="muted">{fileSummary}</span>
      </div>

      <div className="actions">
        <button type="submit" className="button" disabled={isSubmitting}>
          {isSubmitting ? "Uploading..." : "Upload and Index"}
        </button>
      </div>

      {status && <div className="status-ok">{status}</div>}
      {error && <div className="status-error">{error}</div>}
    </form>
  );
}
