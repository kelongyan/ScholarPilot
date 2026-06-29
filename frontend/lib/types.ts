/**
 * Shared frontend type definitions mirroring backend schemas.
 */

export type DocumentStatus =
  | "uploaded"
  | "parsing"
  | "parsed"
  | "indexing"
  | "indexed"
  | "failed";

export interface DocumentResponse {
  doc_id: string;
  title: string;
  source: string;
  status: DocumentStatus;
  page_count: number;
  error_message: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: DocumentResponse[];
}

export interface CitationResponse {
  doc_id: string;
  chunk_id: string;
  section: string;
  page: number;
  quote: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  citations: CitationResponse[];
}

export interface ChatRequest {
  doc_id: string;
  question: string;
}
