"use client";

import { FormEvent, useMemo, useState } from "react";
import { Files, FolderClosed, Upload } from "lucide-react";

import ConfirmDialog from "@/components/app/confirm-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ApiError, uploadDocuments } from "@/lib/api";
import type { ProjectType, UploadResponse, UploadScopeType } from "@/lib/types";

type UploadFormProps = {
  defaultProjectName?: string;
  lockProjectScope?: boolean;
  onUploaded?: (response: UploadResponse) => void;
};

export default function UploadForm({
  defaultProjectName = "",
  lockProjectScope = false,
  onUploaded,
}: UploadFormProps) {
  const [scopeType, setScopeType] = useState<UploadScopeType>("project");
  const [scopeId, setScopeId] = useState(defaultProjectName);
  const [documentType, setDocumentType] = useState("general");
  const [projectType, setProjectType] = useState<ProjectType>("geplant");
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const isLockedProject = lockProjectScope && defaultProjectName.trim().length > 0;

  const effectiveScopeType: UploadScopeType = isLockedProject ? "project" : scopeType;
  const scopeIdPlaceholder = useMemo(() => {
    if (effectiveScopeType === "project") {
      return "e.g. berlin-mitte-deal";
    }
    if (effectiveScopeType === "domain") {
      return "e.g. tax, insurance, corporate";
    }
    return "global";
  }, [effectiveScopeType]);

  const destinationSummary = useMemo(() => {
    const normalizedScopeId = scopeId.trim() || scopeIdPlaceholder;

    if (effectiveScopeType === "project") {
      return `Indexes into project:${normalizedScopeId} and mirrors into shared real-estate/global knowledge.`;
    }

    if (effectiveScopeType === "domain") {
      return `Indexes into domain:${normalizedScopeId} for broader non-project retrieval.`;
    }

    return "Indexes into the global knowledge layer.";
  }, [effectiveScopeType, scopeId, scopeIdPlaceholder]);

  const canReset =
    scopeId !== defaultProjectName ||
    documentType !== "general" ||
    files.length > 0 ||
    projectType !== "geplant" ||
    (!isLockedProject && scopeType !== "project");

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
        `Upload successful. Indexed ${response.chunks_created} chunks in ${response.scope_type}:${response.scope_id}.`,
      );
      setFiles([]);
      onUploaded?.(response);
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

  function resetForm() {
    setStatus("");
    setError("");
    setScopeType("project");
    setScopeId(defaultProjectName);
    setDocumentType("general");
    setProjectType("geplant");
    setFiles([]);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="rounded-2xl border border-border bg-background p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">scope: {effectiveScopeType}</Badge>
          {effectiveScopeType === "project" ? (
            <Badge variant="secondary">project type: {projectType}</Badge>
          ) : null}
        </div>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">{destinationSummary}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="scopeType">Scope Type</Label>
          <Select
            value={effectiveScopeType}
            onValueChange={(value) => setScopeType(value as UploadScopeType)}
            disabled={isLockedProject}
          >
            <SelectTrigger id="scopeType" aria-label="Upload scope type">
              <SelectValue placeholder="Select scope type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="project">project</SelectItem>
              <SelectItem value="domain">domain</SelectItem>
              <SelectItem value="global">global</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="scopeId">Scope ID</Label>
          <Input
            id="scopeId"
            value={scopeId}
            onChange={(event) => setScopeId(event.target.value)}
            placeholder={scopeIdPlaceholder}
            disabled={isLockedProject}
            autoComplete="off"
          />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="documentType">Document Type</Label>
          <Input
            id="documentType"
            value={documentType}
            onChange={(event) => setDocumentType(event.target.value)}
            placeholder="e.g. expose, rent-roll, bilanz, versicherung"
            autoComplete="off"
          />
        </div>

        {effectiveScopeType === "project" ? (
          <div className="space-y-2">
            <Label htmlFor="projectType">Project Type</Label>
            <Select
              value={projectType}
              onValueChange={(value) => setProjectType(value as ProjectType)}
            >
              <SelectTrigger id="projectType" aria-label="Project type">
                <SelectValue placeholder="Select project type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="bestand">bestand</SelectItem>
                <SelectItem value="geplant">geplant</SelectItem>
              </SelectContent>
            </Select>
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-border bg-muted/25 p-4">
            <p className="text-sm font-medium text-foreground">No project type needed</p>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              Project type is only relevant for uploads that belong to a specific asset or deal.
            </p>
          </div>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="documents">Documents</Label>
        <Input
          id="documents"
          type="file"
          multiple
          accept=".pdf,.docx,.xlsx,.pptx,.txt,.md,.csv"
          onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
          aria-describedby="upload-file-help"
        />
        <p id="upload-file-help" className="text-xs text-muted-foreground">
          Supported by the current backend pipeline: PDF, DOCX, XLSX, PPTX, TXT, MD, CSV.
        </p>

        <div className="rounded-2xl border border-border bg-muted/20 p-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Files className="h-4 w-4" aria-hidden="true" />
            <span>{files.length === 0 ? "No files selected yet" : `${files.length} file(s) selected`}</span>
          </div>

          <div className="mt-3 flex min-h-10 flex-wrap gap-2">
            {files.length === 0 ? (
              <div className="inline-flex items-center gap-2 rounded-full border border-dashed border-border px-3 py-1.5 text-sm text-muted-foreground">
                <FolderClosed className="h-4 w-4" aria-hidden="true" />
                Waiting for upload files
              </div>
            ) : (
              files.map((file) => (
                <Badge key={`${file.name}-${file.size}`} variant="outline" className="max-w-full">
                  <span className="truncate">{file.name}</span>
                </Badge>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 pt-1">
        <Button type="submit" disabled={isSubmitting}>
          <Upload className="h-4 w-4" aria-hidden="true" />
          {isSubmitting ? "Uploading..." : "Upload and Index"}
        </Button>
        <ConfirmDialog
          triggerLabel="Reset"
          title="Reset upload form?"
          description="This clears selected files and form fields."
          confirmLabel="Reset form"
          onConfirm={resetForm}
          triggerVariant="outline"
        />
        {!canReset ? (
          <span className="text-sm text-muted-foreground">Form is already clean.</span>
        ) : null}
      </div>

      <div className="space-y-2" aria-live="polite">
        {status ? (
          <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
            {status}
          </p>
        ) : null}
        {error ? (
          <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        ) : null}
      </div>
    </form>
  );
}
