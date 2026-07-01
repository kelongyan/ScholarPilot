"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  KnowledgeOperationEventResponse,
  KnowledgeOperationItemResponse,
  KnowledgeOperationStatus,
} from "@/lib/types";

const SEVERITY_STYLES: Record<string, string> = {
  high: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  medium: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  low: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
};

const STATUS_OPTIONS = [
  { label: "Pending", value: "pending" },
  { label: "All", value: "" },
  { label: "Resolved", value: "resolved" },
  { label: "Ignored", value: "ignored" },
  { label: "Reindexed", value: "reindexed" },
  { label: "Document added", value: "document_added" },
];

const SOURCE_TYPE_OPTIONS = [
  { label: "All sources", value: "" },
  { label: "Question logs", value: "question_log" },
  { label: "Answer feedback", value: "answer_feedback" },
  { label: "Documents", value: "document" },
  { label: "Agent runs", value: "agent_run" },
];

const WORK_TYPE_OPTIONS = [
  { label: "All work", value: "" },
  { label: "Knowledge gaps", value: "knowledge_gap" },
  { label: "Answer quality", value: "answer_quality" },
  { label: "Citation review", value: "citation_review" },
  { label: "Failed documents", value: "failed_document" },
  { label: "Agent warnings", value: "agent_warning" },
];

const ACTIONS: Array<{
  label: string;
  status: KnowledgeOperationStatus;
  note: string;
  requiresDocument?: boolean;
}> = [
  { label: "Resolve", status: "resolved", note: "Marked resolved from operations UI." },
  { label: "Ignore", status: "ignored", note: "Marked ignored from operations UI." },
  {
    label: "Queue reindex",
    status: "reindexed",
    note: "Document reindex queued from operations UI.",
    requiresDocument: true,
  },
  { label: "Doc added", status: "document_added", note: "Supporting document added." },
];

export function KnowledgeOperationsPanel({
  knowledgeBaseId,
  selectedRunId,
  onClearRunFilter,
}: {
  knowledgeBaseId: string | null;
  selectedRunId?: string | null;
  onClearRunFilter?: () => void;
}) {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("pending");
  const [sourceTypeFilter, setSourceTypeFilter] = useState("");
  const [workTypeFilter, setWorkTypeFilter] = useState("");

  const visibleSourceType = selectedRunId ? "agent_run" : sourceTypeFilter;

  const queryKey = [
    "knowledge-operation-items",
    knowledgeBaseId,
    statusFilter,
    visibleSourceType,
    selectedRunId ?? "",
  ];
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey,
    queryFn: () =>
      apiClient.listKnowledgeOperationItems(
        knowledgeBaseId,
        statusFilter || null,
        visibleSourceType || null,
        selectedRunId ?? null
      ),
    staleTime: 10_000,
    enabled: Boolean(knowledgeBaseId),
  });

  const mutation = useMutation({
    mutationFn: ({
      itemId,
      status,
      resolutionNote,
    }: {
      itemId: string;
      status: KnowledgeOperationStatus;
      resolutionNote: string;
    }) =>
      apiClient.updateKnowledgeOperationItem(itemId, {
        status,
        resolution_note: resolutionNote,
      }),
    onSuccess: (item) => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-operation-items"] });
      queryClient.invalidateQueries({ queryKey: ["audit-logs"] });
      if (item.status === "reindexed") {
        queryClient.invalidateQueries({ queryKey: ["documents"] });
      }
    },
  });

  const items = (data?.items ?? []).filter((item) => {
    if (!workTypeFilter) {
      return true;
    }
    return getWorkType(item) === workTypeFilter;
  });
  const totalCount = data?.items.length ?? 0;

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Operations
          </h2>
          <p className="text-[11px] text-zinc-400">
            {items.length}/{totalCount} item(s)
          </p>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          disabled={!knowledgeBaseId || isFetching}
          className="text-xs font-medium text-zinc-500 underline-offset-2 hover:underline disabled:text-zinc-300 dark:text-zinc-400 dark:disabled:text-zinc-700"
        >
          {isFetching ? "Refreshing" : "Refresh"}
        </button>
      </div>

      {selectedRunId && onClearRunFilter && (
        <button
          type="button"
          onClick={onClearRunFilter}
          className="self-start text-[10px] font-medium text-zinc-500 underline-offset-2 hover:underline dark:text-zinc-400"
        >
          Showing Agent run {selectedRunId}
        </button>
      )}

      <select
        value={statusFilter}
        onChange={(event) => setStatusFilter(event.target.value)}
        disabled={!knowledgeBaseId}
        className="rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-xs text-zinc-600 disabled:bg-zinc-50 disabled:text-zinc-300 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:disabled:bg-zinc-900/50"
      >
        {STATUS_OPTIONS.map((option) => (
          <option key={option.label} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      <select
        value={workTypeFilter}
        onChange={(event) => setWorkTypeFilter(event.target.value)}
        disabled={!knowledgeBaseId}
        className="rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-xs text-zinc-600 disabled:bg-zinc-50 disabled:text-zinc-300 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:disabled:bg-zinc-900/50"
      >
        {WORK_TYPE_OPTIONS.map((option) => (
          <option key={option.label} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      <select
        value={visibleSourceType}
        onChange={(event) => setSourceTypeFilter(event.target.value)}
        disabled={!knowledgeBaseId || Boolean(selectedRunId)}
        className="rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-xs text-zinc-600 disabled:bg-zinc-50 disabled:text-zinc-300 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:disabled:bg-zinc-900/50"
      >
        {SOURCE_TYPE_OPTIONS.map((option) => (
          <option key={option.label} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {!knowledgeBaseId ? (
        <EmptyState text="Select a knowledge base to view operations." />
      ) : isLoading ? (
        <p className="text-sm text-zinc-400 dark:text-zinc-500">Loading...</p>
      ) : isError ? (
        <p className="text-sm text-red-500">Failed to load operation items.</p>
      ) : items.length === 0 ? (
        <EmptyState text="No operation items" />
      ) : (
        <>
          {mutation.isError && (
            <p className="rounded-md border border-red-200 bg-red-50 px-2 py-1.5 text-[11px] text-red-600 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
              {mutation.error.message}
            </p>
          )}
          <ul className="flex max-h-72 flex-col gap-2 overflow-auto pr-1">
            {items.slice(0, 8).map((item) => (
              <li key={item.item_id}>
                <OperationItemCard
                  item={item}
                  isUpdating={mutation.isPending}
                  onUpdate={(status, note) =>
                    mutation.mutate({
                      itemId: item.item_id,
                      status,
                      resolutionNote: note,
                    })
                  }
                />
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function OperationItemCard({
  item,
  isUpdating,
  onUpdate,
}: {
  item: KnowledgeOperationItemResponse;
  isUpdating: boolean;
  onUpdate: (status: KnowledgeOperationStatus, note: string) => void;
}) {
  const [showEvents, setShowEvents] = useState(false);
  const actions = ACTIONS.filter((action) => {
    if (!action.requiresDocument) {
      return true;
    }
    return Boolean(item.doc_id) || item.suggestion_type === "reindex_document";
  });
  const eventsQuery = useQuery({
    queryKey: ["knowledge-operation-item-events", item.item_id],
    queryFn: () => apiClient.listKnowledgeOperationItemEvents(item.item_id),
    enabled: showEvents,
    staleTime: 10_000,
  });
  const events = eventsQuery.data?.events ?? [];

  return (
    <div className="rounded-md border border-zinc-200 p-2 text-sm dark:border-zinc-800">
      <div className="mb-1 flex items-center justify-between gap-2">
        <span className="line-clamp-1 font-medium text-zinc-800 dark:text-zinc-100">
          {item.title}
        </span>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${
            SEVERITY_STYLES[item.severity] ?? SEVERITY_STYLES.low
          }`}
        >
          {item.severity}
        </span>
      </div>
      <p className="line-clamp-2 text-xs text-zinc-500 dark:text-zinc-400">
        {item.description}
      </p>
      <p className="mt-1 line-clamp-2 text-xs text-zinc-600 dark:text-zinc-300">
        {item.suggested_action}
      </p>
      <div className="mt-2 flex items-center justify-between gap-2 text-[10px] text-zinc-400">
        <span>{formatLabel(getWorkType(item))}</span>
        <span>{formatLabel(item.status)}</span>
      </div>
      <div className="mt-1 flex items-center justify-between gap-2 text-[10px] text-zinc-400">
        <span>{item.signal_count} signal(s)</span>
        {item.last_signal_at && <span>{formatShortDate(item.last_signal_at)}</span>}
      </div>
      {item.status === "pending" && (
        <div className="mt-2 grid grid-cols-2 gap-1">
          {actions.map((action) => (
            <button
              key={action.status}
              type="button"
              disabled={isUpdating}
              onClick={() => onUpdate(action.status, action.note)}
              className="rounded border border-zinc-300 px-2 py-1 text-[10px] font-medium text-zinc-600 hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
      {item.resolution_note && (
        <p className="mt-2 line-clamp-2 text-[10px] text-zinc-400">
          {item.resolution_note}
        </p>
      )}
      <button
        type="button"
        onClick={() => setShowEvents((value) => !value)}
        className="mt-2 text-[10px] font-medium text-zinc-500 underline-offset-2 hover:underline dark:text-zinc-400"
      >
        {showEvents ? "Hide history" : "Show history"}
      </button>
      {showEvents && (
        <OperationEventList
          events={events}
          isLoading={eventsQuery.isLoading}
          isError={eventsQuery.isError}
        />
      )}
    </div>
  );
}

function OperationEventList({
  events,
  isLoading,
  isError,
}: {
  events: KnowledgeOperationEventResponse[];
  isLoading: boolean;
  isError: boolean;
}) {
  if (isLoading) {
    return <p className="mt-2 text-[10px] text-zinc-400">Loading history...</p>;
  }
  if (isError) {
    return <p className="mt-2 text-[10px] text-red-500">Failed to load history.</p>;
  }
  if (events.length === 0) {
    return <p className="mt-2 text-[10px] text-zinc-400">No history yet.</p>;
  }
  return (
    <ul className="mt-2 flex flex-col gap-1 border-t border-zinc-100 pt-2 dark:border-zinc-800">
      {events.slice(0, 4).map((event) => (
        <li key={event.event_id} className="text-[10px] text-zinc-500 dark:text-zinc-400">
          <div className="flex items-center justify-between gap-2">
            <span className="font-medium text-zinc-600 dark:text-zinc-300">
              {formatLabel(event.event_type)}
            </span>
            <span>{formatShortDate(event.created_at)}</span>
          </div>
          {event.note && <p className="line-clamp-2">{event.note}</p>}
        </li>
      ))}
    </ul>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-zinc-300 p-4 text-center text-sm text-zinc-400 dark:border-zinc-700 dark:text-zinc-500">
      {text}
    </div>
  );
}

function formatLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function getWorkType(item: KnowledgeOperationItemResponse): string {
  if (item.suggestion_type === "faq_draft") {
    return "knowledge_gap";
  }
  if (item.suggestion_type === "answer_quality_review") {
    return "answer_quality";
  }
  if (item.suggestion_type === "citation_review") {
    return "citation_review";
  }
  if (item.suggestion_type === "reindex_document") {
    return "failed_document";
  }
  if (item.suggestion_type === "agent_review") {
    return "agent_warning";
  }
  return item.source_type;
}

function formatShortDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
