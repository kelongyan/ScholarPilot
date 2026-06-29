/**
 * API client for the ScholarPilot backend.
 */

import type {
  ChatRequest,
  ChatResponse,
  DocumentListResponse,
  DocumentResponse,
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
  async uploadDocument(file: File): Promise<DocumentResponse> {
    const form = new FormData();
    form.append("file", file);
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
  async listDocuments(): Promise<DocumentListResponse> {
    const res = await fetch(`${this.baseUrl}/documents`);
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
}

export const apiClient = new ApiClient();
