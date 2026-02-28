"use client";

import { FormEvent, useMemo, useState } from "react";

import { ApiError, uploadDocuments } from "@/lib/api";
import type { ProjectType } from "@/lib/types";

type UploadFormProps = {
  defaultProjectName?: string;
  onUploaded?: () => void;
};

export default function UploadForm({
  defaultProjectName = "",
  onUploaded,
}: UploadFormProps) {
  const [projectName, setProjectName] = useState(defaultProjectName);
  const [projectType, setProjectType] = useState<ProjectType>("potenziell");
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");

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

    if (!projectName.trim()) {
      setError("Project name is required.");
      return;
    }
    if (files.length === 0) {
      setError("Select at least one file.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await uploadDocuments({
        projectName: projectName.trim(),
        projectType,
        files,
      });
      setStatus(
        `Upload complete: ${response.chunks_created} chunks indexed for ${response.project_name}.`,
      );
      setFiles([]);
      onUploaded?.();
    } catch (uploadError) {
      if (uploadError instanceof ApiError) {
        setError(uploadError.detail);
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
        <label htmlFor="projectName">Project Name</label>
        <input
          id="projectName"
          value={projectName}
          onChange={(event) => setProjectName(event.target.value)}
          placeholder="e.g. Berlin-Mitte Deal"
        />
      </div>

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
