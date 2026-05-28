export type ProjectType = "bestand" | "geplant" | "potenziell";
export type ChatScope = "project" | "realestate_global" | "global";
export type UploadScopeType = "project" | "domain" | "global";

export type ProjectInfo = {
  project_name: string;
  project_type: ProjectType;
  created_at: string | null;
  updated_at: string | null;
  files_count: number;
  text_backups_count: number;
  table_name: string;
  has_vector_index: boolean;
  chunks_indexed: number;
};

export type ProjectsResponse = {
  projects: ProjectInfo[];
  count: number;
};

export type UploadResponse = {
  message: string;
  project_name: string;
  project_type: ProjectType;
  scope_type: UploadScopeType;
  scope_id: string;
  document_type: string;
  chunks_created: number;
};

export type ChatEvidence = {
  source: string;
  file_name?: string;
  project_name?: string;
  project_type?: string;
  scope_type?: string;
  scope_id?: string;
  document_type?: string;
  excerpt: string;
  chunk_id: string | null;
  score: number | null;
};

export type GraphFact = {
  kind: string;
  label?: string | null;
  text: string;
};

export type ChatResponse = {
  answer: string;
  scope: ChatScope | string;
  effective_scope: string;
  sources: string[];
  evidence: ChatEvidence[];
  graph_facts?: GraphFact[];
};

export type ChatRequest = {
  query: string;
  scope: ChatScope;
  top_k?: number;
  project_name?: string;
};

export type KnowledgeStatus = {
  projects: {
    count: number;
  };
  metadata: {
    project_count: number;
    document_count: number;
    graph_indexed_documents: number;
  };
  vectorstores: {
    realestate_global_available: boolean;
    global_brain_available: boolean;
  };
  graph: {
    enabled: boolean;
    package_available: boolean;
    configured: boolean;
    active: boolean;
    connected: boolean;
    database: string;
    uri: string | null;
    node_count: number;
    entity_count: number;
    relationship_count: number;
  };
};
