/**
 * API client for the Kairos backend.
 */

import type {
  AgentRunRequest,
  AgentRunResponse,
  AnswerFeedbackRequest,
  AnswerFeedbackResponse,
  ChatRequest,
  ChatResponse,
  DocumentListResponse,
  DocumentResponse,
  KnowledgeBaseCreateRequest,
  KnowledgeBaseListResponse,
  KnowledgeBaseResponse,
  KnowledgeBaseUpdateRequest,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiClient {
  constructor(private readonly baseUrl: string = API_BASE_URL) {}

  /** Check whether the backend is reachable. */
  async health(): Promise<{ status: string }> {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) {
      throw new Error(`Health check failed: ${res.status}`);
    }
    return res.json() as Promise<{ status: string }>;
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
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`List failed: ${res.status}`);
    }
    return res.json() as Promise<DocumentListResponse>;
  }

  /** Get a document's metadata and status. */
  async getDocument(docId: string): Promise<DocumentResponse> {
    const res = await fetch(`${this.baseUrl}/documents/${docId}`);
    if (!res.ok) {
      throw new Error(`Get document failed: ${res.status}`);
    }
    return res.json() as Promise<DocumentResponse>;
  }

  /** Ask a question about a document. */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const res = await fetch(`${this.baseUrl}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Agent run failed: ${res.status} ${detail}`);
    }
    return res.json() as Promise<AgentRunResponse>;
  }

  async listKnowledgeBases(): Promise<KnowledgeBaseListResponse> {
    const res = await fetch(`${this.baseUrl}/knowledge-bases`);
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
      headers: { "Content-Type": "application/json" },
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
      headers: { "Content-Type": "application/json" },
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
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Submit feedback failed: ${res.status} ${detail}`);
    }
    return res.json() as Promise<AnswerFeedbackResponse>;
  }
}

export const apiClient = new ApiClient();
