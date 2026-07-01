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

export type DocumentLifecycleStatus = "active" | "archived" | "deleted";

export interface DocumentResponse {
  doc_id: string;
  knowledge_base_id: string;
  title: string;
  source: string;
  content_hash: string;
  version: number;
  lifecycle_status: DocumentLifecycleStatus;
  replaces_doc_id: string;
  replaced_by_doc_id: string;
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

export interface ChatTraceResponse {
  trace_id: string;
  question_log_id: string;
  query: string;
  rewritten_query: string;
  dense_results_json: RetrievalHitResponse[];
  sparse_results_json: RetrievalHitResponse[];
  fused_results_json: RetrievalHitResponse[];
  reranked_results_json: RetrievalHitResponse[];
  evidence_pack_json: EvidenceItemResponse[];
  answer: string;
  citations_json: CitationResponse[];
  answer_status: string;
  model: string;
  latency_ms: number;
  created_at: string;
  updated_at: string;
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

export interface AgentRunListResponse {
  agent_runs: AgentRunResponse[];
}

export interface AgentRunListFilters {
  knowledge_base_id?: string | null;
  route?: string | null;
  status?: string | null;
  answer_status?: string | null;
  created_from?: string | null;
  created_to?: string | null;
}

export interface AuditLogResponse {
  audit_id: string;
  actor_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  knowledge_base_id?: string | null;
  detail_json: Record<string, unknown>;
  created_at: string;
}

export interface AuditLogListResponse {
  audit_logs: AuditLogResponse[];
}

export interface AuditLogListFilters {
  knowledge_base_id?: string | null;
  action?: string | null;
  resource_type?: string | null;
  resource_id?: string | null;
  actor_id?: string | null;
  created_from?: string | null;
  created_to?: string | null;
}

export type UserRole = "user" | "kb_manager" | "admin";

export interface CurrentUserResponse {
  actor_id: string;
  role: UserRole;
  knowledge_base_ids?: string[] | null;
  auth_enabled: boolean;
}

export interface UserAccountResponse {
  user_id: string;
  email: string;
  display_name: string;
  status: string;
  role: string;
  created_at: string;
  updated_at: string;
}

export type KnowledgeBaseMemberRole = "viewer" | "contributor" | "manager" | "owner";
export type KnowledgeBaseMemberStatus = "active" | "disabled";

export interface KnowledgeBaseMemberResponse {
  membership_id: string;
  knowledge_base_id: string;
  user_id: string;
  role: KnowledgeBaseMemberRole;
  status: KnowledgeBaseMemberStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBaseMemberListResponse {
  members: KnowledgeBaseMemberResponse[];
}

export interface KnowledgeBaseMemberUpsertRequest {
  role: KnowledgeBaseMemberRole;
  status?: KnowledgeBaseMemberStatus;
}

export interface EvaluationDatasetQuestionResponse {
  sequence: number;
  question: string;
  expected_keywords: string[];
  notes: string;
}

export interface EvaluationDatasetResponse {
  dataset_key: string;
  name: string;
  description: string;
  source_uri: string;
  question_count: number;
  created_at: string;
  updated_at: string;
}

export interface EvaluationDatasetDetailResponse extends EvaluationDatasetResponse {
  questions: EvaluationDatasetQuestionResponse[];
}

export interface EvaluationDatasetListResponse {
  evaluation_datasets: EvaluationDatasetResponse[];
}

export type EvaluationExecutionMode = "chat" | "agent";
export type EvaluationRunStatus = "running" | "completed" | "failed";
export type EvaluationItemStatus = "passed" | "failed" | "error";

export interface EvaluationRunCreateRequest {
  dataset_key?: string;
  knowledge_base_id?: string | null;
  doc_id?: string | null;
  execution_mode?: EvaluationExecutionMode;
  max_steps?: number;
}

export interface EvaluationRunItemResponse {
  item_id: string;
  sequence: number;
  question: string;
  expected_keywords: string[];
  matched_keywords: string[];
  missing_keywords: string[];
  metrics_json: Record<string, unknown>;
  answer: string;
  answer_status: string;
  execution_route: string;
  status: EvaluationItemStatus;
  error_message: string;
  latency_ms: number;
  question_log_id?: string | null;
  chat_trace_id?: string | null;
  agent_run_id?: string | null;
  created_at: string;
}

export interface EvaluationRunResponse {
  run_id: string;
  dataset_key: string;
  dataset_name: string;
  knowledge_base_id?: string | null;
  doc_id?: string | null;
  execution_mode: EvaluationExecutionMode;
  status: EvaluationRunStatus;
  question_count: number;
  passed_count: number;
  failed_count: number;
  average_latency_ms: number;
  dataset_version: string;
  config_snapshot_json: Record<string, unknown>;
  pass_rate: number;
  summary_json: Record<string, unknown>;
  metrics_json: Record<string, unknown>;
  previous_run_id?: string | null;
  metric_deltas: Record<string, number>;
  items: EvaluationRunItemResponse[];
  created_at: string;
  updated_at: string;
}

export interface EvaluationRunListResponse {
  evaluation_runs: EvaluationRunResponse[];
}

export interface EvaluationRunListFilters {
  dataset_key?: string | null;
  knowledge_base_id?: string | null;
  doc_id?: string | null;
  execution_mode?: string | null;
  status?: string | null;
  created_from?: string | null;
  created_to?: string | null;
}

export interface ObservabilityEvaluationSummaryResponse {
  run_id: string;
  dataset_key: string;
  dataset_version: string;
  execution_mode: string;
  pass_rate: number;
  average_keyword_coverage: number;
  average_recall_at_k: number;
  average_mrr: number;
  average_citation_accuracy: number;
  average_faithfulness: number;
  average_answer_relevance: number;
  answer_rate: number;
  trace_rate: number;
  error_rate: number;
  average_latency_ms: number;
  created_at: string;
}

export interface ObservabilityRegressionAlertResponse {
  metric: string;
  severity: string;
  current_value: number;
  previous_value: number;
  delta: number;
  message: string;
}

export interface ObservabilityLatencyBucketResponse {
  label: string;
  min_ms: number;
  max_ms?: number | null;
  count: number;
}

export interface ObservabilitySummaryResponse {
  knowledge_base_id?: string | null;
  latest_evaluation?: ObservabilityEvaluationSummaryResponse | null;
  evaluation_trend: ObservabilityEvaluationSummaryResponse[];
  regression_alerts: ObservabilityRegressionAlertResponse[];
  latency_buckets: ObservabilityLatencyBucketResponse[];
  question_count: number;
  answered_count: number;
  unresolved_answer_count: number;
  no_answer_rate: number;
  feedback_count: number;
  negative_feedback_count: number;
  negative_feedback_rate: number;
  trace_count: number;
  average_trace_latency_ms: number;
  pending_operation_count: number;
  high_severity_pending_count: number;
  operation_signal_count: number;
  generated_at: string;
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

export type KnowledgeOperationStatus =
  | "pending"
  | "resolved"
  | "ignored"
  | "reindexed"
  | "document_added";

export interface KnowledgeOperationItemResponse {
  item_id: string;
  knowledge_base_id?: string | null;
  doc_id?: string | null;
  question_log_id?: string | null;
  agent_run_id?: string | null;
  source_type: string;
  source_id: string;
  suggestion_type: string;
  aggregate_key: string;
  signal_count: number;
  last_signal_at?: string | null;
  severity: string;
  title: string;
  description: string;
  suggested_action: string;
  status: KnowledgeOperationStatus;
  resolution_note: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeOperationItemListResponse {
  items: KnowledgeOperationItemResponse[];
}

export interface KnowledgeOperationItemUpdateRequest {
  status: KnowledgeOperationStatus;
  resolution_note?: string;
}

export interface KnowledgeOperationEventResponse {
  event_id: string;
  item_id: string;
  knowledge_base_id?: string | null;
  event_type: string;
  actor_id: string;
  source_type: string;
  source_id: string;
  suggestion_type: string;
  status: string;
  note: string;
  detail_json: Record<string, unknown>;
  created_at: string;
}

export interface KnowledgeOperationEventListResponse {
  events: KnowledgeOperationEventResponse[];
}

export interface KnowledgeOperationDraftResponse {
  draft_id: string;
  item_id: string;
  knowledge_base_id?: string | null;
  doc_id?: string | null;
  question_log_id?: string | null;
  draft_type: string;
  status: string;
  title: string;
  question: string;
  answer: string;
  source_note: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeOperationDraftListResponse {
  drafts: KnowledgeOperationDraftResponse[];
}

export interface KnowledgeOperationSuggestionResponse {
  suggestion_id: string;
  item_id: string;
  knowledge_base_id?: string | null;
  doc_id?: string | null;
  question_log_id?: string | null;
  agent_run_id?: string | null;
  source_type: string;
  source_id: string;
  suggestion_type: string;
  aggregate_key: string;
  signal_count: number;
  last_signal_at?: string | null;
  severity: string;
  title: string;
  description: string;
  suggested_action: string;
  status: KnowledgeOperationStatus;
  resolution_note: string;
  evidence: Array<Record<string, unknown>>;
  created_at?: string | null;
}

export interface KnowledgeOperationSuggestionListResponse {
  suggestions: KnowledgeOperationSuggestionResponse[];
}
