import type {
  ChatRequest,
  ChatResponse,
  KnowledgeStatus,
  ProjectInfo,
  ProjectsResponse,
  ProjectType,
  UploadScopeType,
  UploadResponse,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Network request failed.";
    throw new ApiError(
      0,
      `Cannot reach backend at ${API_BASE_URL}. Check backend process, CORS, and URL. (${message})`,
    );
  }

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const errorBody = await response.json();
      if (typeof errorBody?.detail === "string") {
        detail = errorBody.detail;
      }
    } catch {
      // Keep the status message fallback.
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

export async function fetchProjects(): Promise<ProjectInfo[]> {
  const response = await requestJson<ProjectsResponse>("/projects/list");
  return response.projects;
}

export async function fetchProjectInfo(projectName: string): Promise<ProjectInfo> {
  const encodedProjectName = encodeURIComponent(projectName);
  return requestJson<ProjectInfo>(`/projects/info?project_name=${encodedProjectName}`);
}

export async function uploadDocuments(input: {
  scopeType: UploadScopeType;
  scopeId: string;
  documentType: string;
  projectName?: string;
  projectType?: ProjectType;
  files: File[];
}): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("scope_type", input.scopeType);
  formData.append("scope_id", input.scopeId);
  formData.append("document_type", input.documentType);

  if (input.projectName) {
    formData.append("project_name", input.projectName);
  }
  if (input.projectType) {
    formData.append("project_type", input.projectType);
  }

  for (const file of input.files) {
    formData.append("files", file);
  }

  return requestJson<UploadResponse>("/upload", {
    method: "POST",
    body: formData,
  });
}

export async function sendChat(payload: ChatRequest): Promise<ChatResponse> {
  return requestJson<ChatResponse>("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchKnowledgeStatus(): Promise<KnowledgeStatus> {
  return requestJson<KnowledgeStatus>("/system/knowledge-status");
}
