/**
 * API client for the Kairos backend.
 */

import type {
  AgentRunListFilters,
  AgentRunListResponse,
  AgentRunRequest,
  AgentRunResponse,
  AuditLogListFilters,
  AuditLogListResponse,
  AnswerFeedbackRequest,
  AnswerFeedbackResponse,
  ChatRequest,
  ChatResponse,
  CurrentUserResponse,
  DocumentListResponse,
  DocumentResponse,
  EvaluationDatasetDetailResponse,
  EvaluationDatasetListResponse,
  EvaluationRunCreateRequest,
  EvaluationRunListFilters,
  EvaluationRunListResponse,
  EvaluationRunResponse,
  KnowledgeBaseCreateRequest,
  KnowledgeBaseListResponse,
  KnowledgeBaseResponse,
  KnowledgeBaseUpdateRequest,
  KnowledgeOperationItemListResponse,
  KnowledgeOperationItemResponse,
  KnowledgeOperationItemUpdateRequest,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const AUTH_TOKEN = process.env.NEXT_PUBLIC_KAIROS_AUTH_TOKEN ?? "";

export class ApiClient {
  constructor(
    private readonly baseUrl: string = API_BASE_URL,
    private readonly authToken: string = AUTH_TOKEN
  ) {}

  private headers(init?: HeadersInit): HeadersInit {
    const headers = new Headers(init);
    if (this.authToken) {
      headers.set("Authorization", `Bearer ${this.authToken}`);
    }
    return headers;
  }

  private jsonHeaders(): HeadersInit {
    return this.headers({ "Content-Type": "application/json" });
  }

  /** Check whether the backend is reachable. */
  async health(): Promise<{ status: string }> {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) {
      throw new Error(`Health check failed: ${res.status}`);
    }
    return res.json() as Promise<{ status: string }>;
  }

  async getCurrentUser(): Promise<CurrentUserResponse> {
    const res = await fetch(`${this.baseUrl}/auth/me`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      throw new Error(`Get current user failed: ${res.status}`);
    }
    return res.json() as Promise<CurrentUserResponse>;
  }

  /** Upload a PDF and start async processing. */
  async uploadDocument(
    file: File,
    knowledgeBaseId?: string | null
  ): Promise<DocumentResponse> {
    const form = new FormData();
    form.append("file", file);
    if (knowledgeBaseId) {
      form.append("knowledge_base_id", knowledgeBaseId);
    }
    const res = await fetch(`${this.baseUrl}/documents/upload`, {
      method: "POST",
      headers: this.headers(),
      body: form,
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Upload failed: ${res.status} ${detail}`);
    }
    return res.json() as Promise<DocumentResponse>;
  }

  /** List all documents. */
  async listDocuments(knowledgeBaseId?: string | null): Promise<DocumentListResponse> {
    const url = new URL(`${this.baseUrl}/documents`);
    if (knowledgeBaseId) {
      url.searchParams.set("knowledge_base_id", knowledgeBaseId);
    }
    const res = await fetch(url, { headers: this.headers() });
    if (!res.ok) {
      throw new Error(`List failed: ${res.status}`);
    }
    return res.json() as Promise<DocumentListResponse>;
  }

  /** Get a document's metadata and status. */
  async getDocument(docId: string): Promise<DocumentResponse> {
    const res = await fetch(`${this.baseUrl}/documents/${docId}`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      throw new Error(`Get document failed: ${res.status}`);
    }
    return res.json() as Promise<DocumentResponse>;
  }

  /** Ask a question about a document. */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const res = await fetch(`${this.baseUrl}/chat`, {
      method: "POST",
      headers: this.jsonHeaders(),
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Chat failed: ${res.status} ${detail}`);
    }
    return res.json() as Promise<ChatResponse>;
  }

  /** Run a controlled Agent workflow over a document or knowledge base. */
  async runAgent(request: AgentRunRequest): Promise<AgentRunResponse> {
    const res = await fetch(`${this.baseUrl}/agent-runs`, {
      method: "POST",
      headers: this.jsonHeaders(),
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Agent run failed: ${res.status} ${detail}`);
    }
    return res.json() as Promise<AgentRunResponse>;
  }

  async listAgentRuns(
    filters: AgentRunListFilters = {}
  ): Promise<AgentRunListResponse> {
    const url = new URL(`${this.baseUrl}/agent-runs`);
    for (const [key, value] of Object.entries(filters)) {
      if (value) {
        url.searchParams.set(key, value);
      }
    }
    const res = await fetch(url, { headers: this.headers() });
    if (!res.ok) {
      throw new Error(`List Agent runs failed: ${res.status}`);
    }
    return res.json() as Promise<AgentRunListResponse>;
  }

  async getAgentRun(runId: string): Promise<AgentRunResponse> {
    const res = await fetch(`${this.baseUrl}/agent-runs/${runId}`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      throw new Error(`Get Agent run failed: ${res.status}`);
    }
    return res.json() as Promise<AgentRunResponse>;
  }

  async listAuditLogs(
    filters: AuditLogListFilters = {}
  ): Promise<AuditLogListResponse> {
    const url = new URL(`${this.baseUrl}/audit-logs`);
    for (const [key, value] of Object.entries(filters)) {
      if (value) {
        url.searchParams.set(key, value);
      }
    }
    const res = await fetch(url, { headers: this.headers() });
    if (!res.ok) {
      throw new Error(`List audit logs failed: ${res.status}`);
    }
    return res.json() as Promise<AuditLogListResponse>;
  }

  async listEvaluationDatasets(): Promise<EvaluationDatasetListResponse> {
    const res = await fetch(`${this.baseUrl}/evaluations/datasets`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      throw new Error(`List evaluation datasets failed: ${res.status}`);
    }
    return res.json() as Promise<EvaluationDatasetListResponse>;
  }

  async getEvaluationDataset(
    datasetKey: string
  ): Promise<EvaluationDatasetDetailResponse> {
    const res = await fetch(`${this.baseUrl}/evaluations/datasets/${datasetKey}`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      throw new Error(`Get evaluation dataset failed: ${res.status}`);
    }
    return res.json() as Promise<EvaluationDatasetDetailResponse>;
  }

  async createEvaluationRun(
    request: EvaluationRunCreateRequest
  ): Promise<EvaluationRunResponse> {
    const res = await fetch(`${this.baseUrl}/evaluations/runs`, {
      method: "POST",
      headers: this.jsonHeaders(),
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Create evaluation run failed: ${res.status} ${detail}`);
    }
    return res.json() as Promise<EvaluationRunResponse>;
  }

  async listEvaluationRuns(
    filters: EvaluationRunListFilters = {}
  ): Promise<EvaluationRunListResponse> {
    const url = new URL(`${this.baseUrl}/evaluations/runs`);
    for (const [key, value] of Object.entries(filters)) {
      if (value) {
        url.searchParams.set(key, value);
      }
    }
    const res = await fetch(url, { headers: this.headers() });
    if (!res.ok) {
      throw new Error(`List evaluation runs failed: ${res.status}`);
    }
    return res.json() as Promise<EvaluationRunListResponse>;
  }

  async getEvaluationRun(runId: string): Promise<EvaluationRunResponse> {
    const res = await fetch(`${this.baseUrl}/evaluations/runs/${runId}`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      throw new Error(`Get evaluation run failed: ${res.status}`);
    }
    return res.json() as Promise<EvaluationRunResponse>;
  }

  async listKnowledgeBases(): Promise<KnowledgeBaseListResponse> {
    const res = await fetch(`${this.baseUrl}/knowledge-bases`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      throw new Error(`List knowledge bases failed: ${res.status}`);
    }
    return res.json() as Promise<KnowledgeBaseListResponse>;
  }

  async createKnowledgeBase(
    request: KnowledgeBaseCreateRequest
  ): Promise<KnowledgeBaseResponse> {
    const res = await fetch(`${this.baseUrl}/knowledge-bases`, {
      method: "POST",
      headers: this.jsonHeaders(),
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Create knowledge base failed: ${res.status} ${detail}`);
    }
    return res.json() as Promise<KnowledgeBaseResponse>;
  }

  async updateKnowledgeBase(
    knowledgeBaseId: string,
    request: KnowledgeBaseUpdateRequest
  ): Promise<KnowledgeBaseResponse> {
    const res = await fetch(`${this.baseUrl}/knowledge-bases/${knowledgeBaseId}`, {
      method: "PATCH",
      headers: this.jsonHeaders(),
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Update knowledge base failed: ${res.status} ${detail}`);
    }
    return res.json() as Promise<KnowledgeBaseResponse>;
  }

  async submitFeedback(
    questionLogId: string,
    request: AnswerFeedbackRequest
  ): Promise<AnswerFeedbackResponse> {
    const res = await fetch(`${this.baseUrl}/question-logs/${questionLogId}/feedback`, {
      method: "POST",
      headers: this.jsonHeaders(),
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Submit feedback failed: ${res.status} ${detail}`);
    }
    return res.json() as Promise<AnswerFeedbackResponse>;
  }

  async listKnowledgeOperationItems(
    knowledgeBaseId?: string | null,
    status?: string | null
  ): Promise<KnowledgeOperationItemListResponse> {
    const url = new URL(`${this.baseUrl}/knowledge-operations/items`);
    if (knowledgeBaseId) {
      url.searchParams.set("knowledge_base_id", knowledgeBaseId);
    }
    if (status) {
      url.searchParams.set("status", status);
    }
    const res = await fetch(url, { headers: this.headers() });
    if (!res.ok) {
      throw new Error(`List knowledge operation items failed: ${res.status}`);
    }
    return res.json() as Promise<KnowledgeOperationItemListResponse>;
  }

  async updateKnowledgeOperationItem(
    itemId: string,
    request: KnowledgeOperationItemUpdateRequest
  ): Promise<KnowledgeOperationItemResponse> {
    const res = await fetch(`${this.baseUrl}/knowledge-operations/items/${itemId}`, {
      method: "PATCH",
      headers: this.jsonHeaders(),
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Update knowledge operation item failed: ${res.status} ${detail}`);
    }
    return res.json() as Promise<KnowledgeOperationItemResponse>;
  }
}

export const apiClient = new ApiClient();
