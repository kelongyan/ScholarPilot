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
  knowledge_base_id: string;
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

export interface RetrievalHitResponse {
  doc_id: string;
  chunk_id: string;
  section: string;
  page_start: number;
  page_end: number;
  chunk_type: string;
  chunk_index: number;
  score: number;
  retrieval_source: string;
  text: string;
}

export type EvidenceItemResponse = RetrievalHitResponse;

export interface RetrievalTraceResponse {
  query: string;
  rewritten_query: string;
  dense_results: RetrievalHitResponse[];
  sparse_results: RetrievalHitResponse[];
  fused_results: RetrievalHitResponse[];
  reranked_results: RetrievalHitResponse[];
  evidence_pack: EvidenceItemResponse[];
}

export interface ChatResponse {
  answer: string;
  citations: CitationResponse[];
  trace?: RetrievalTraceResponse | null;
  question_log_id?: string | null;
}

export interface ChatRequest {
  doc_id?: string | null;
  knowledge_base_id?: string | null;
  question: string;
}

export type AgentRunMode = "auto" | "short" | "multi_agent";

export interface AgentRunRequest {
  doc_id?: string | null;
  knowledge_base_id?: string | null;
  question: string;
  mode?: AgentRunMode;
  max_steps?: number;
}

export interface AgentStepResponse {
  sequence: number;
  agent_name: string;
  status: string;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown>;
  latency_ms: number;
  error_message: string;
}

export interface AgentRunResponse {
  run_id: string;
  route: string;
  status: string;
  doc_id?: string | null;
  knowledge_base_id?: string | null;
  question: string;
  answer: string;
  answer_status: string;
  citations: CitationResponse[];
  trace?: RetrievalTraceResponse | null;
  agent_steps: AgentStepResponse[];
  question_log_id?: string | null;
  chat_trace_id?: string | null;
  total_latency_ms: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface KnowledgeBaseResponse {
  knowledge_base_id: string;
  name: string;
  description: string;
  status: string;
  owner_id: string;
  visibility: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBaseListResponse {
  knowledge_bases: KnowledgeBaseResponse[];
}

export interface KnowledgeBaseCreateRequest {
  name: string;
  description?: string;
  status?: string;
  owner_id?: string;
  visibility?: string;
}

export interface KnowledgeBaseUpdateRequest {
  name?: string | null;
  description?: string | null;
  status?: string | null;
  owner_id?: string | null;
  visibility?: string | null;
}

export interface QuestionLogResponse {
  question_log_id: string;
  doc_id?: string | null;
  knowledge_base_id?: string | null;
  question: string;
  answer: string;
  answer_status: string;
  citations_json: Record<string, unknown>[];
  created_at: string;
  updated_at: string;
}

export interface AnswerFeedbackRequest {
  useful?: boolean | null;
  citation_accurate?: boolean | null;
}

export interface AnswerFeedbackResponse {
  feedback_id: string;
  question_log_id: string;
  useful?: boolean | null;
  citation_accurate?: boolean | null;
  created_at: string;
  updated_at: string;
}
