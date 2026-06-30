"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { AuditLogListFilters, AuditLogResponse } from "@/lib/types";

const ACTIONS = [
  { label: "All actions", value: "" },
  { label: "Document uploaded", value: "document.uploaded" },
  { label: "Document reindexed", value: "document.reindexed" },
  { label: "Feedback submitted", value: "feedback.submitted" },
  { label: "Agent run created", value: "agent_run.created" },
  { label: "Agent run viewed", value: "agent_run.viewed" },
  {
    label: "Operation updated",
    value: "knowledge_operation_item.updated",
  },
];

const RESOURCE_TYPES = [
  { label: "All resources", value: "" },
  { label: "Documents", value: "document" },
  { label: "Feedback", value: "answer_feedback" },
  { label: "Agent runs", value: "agent_run" },
  { label: "Operations", value: "knowledge_operation_item" },
];

export function AuditLogPanel({
  knowledgeBaseId,
}: {
  knowledgeBaseId: string | null;
}) {
  const [scopeToCurrentKb, setScopeToCurrentKb] = useState(true);
  const [action, setAction] = useState("");
  const [resourceType, setResourceType] = useState("");

  const filters: AuditLogListFilters = useMemo(
    () => ({
      knowledge_base_id: scopeToCurrentKb ? knowledgeBaseId : null,
      action,
      resource_type: resourceType,
    }),
    [action, knowledgeBaseId, resourceType, scopeToCurrentKb]
  );

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["audit-logs", filters],
    queryFn: () => apiClient.listAuditLogs(filters),
    staleTime: 10_000,
  });

  const logs = data?.audit_logs ?? [];

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          Audit Logs
        </h2>
        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="text-xs font-medium text-zinc-500 underline-offset-2 hover:underline disabled:text-zinc-300 dark:text-zinc-400 dark:disabled:text-zinc-700"
        >
          {isFetching ? "Refreshing" : "Refresh"}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <label className="col-span-2 flex items-center gap-2 text-zinc-500 dark:text-zinc-400">
          <input
            type="checkbox"
            checked={scopeToCurrentKb}
            disabled={!knowledgeBaseId}
            onChange={(event) => setScopeToCurrentKb(event.target.checked)}
            className="h-3.5 w-3.5"
          />
          Current knowledge base
        </label>

        <select
          value={action}
          onChange={(event) => setAction(event.target.value)}
          className="min-w-0 rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
        >
          {ACTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <select
          value={resourceType}
          onChange={(event) => setResourceType(event.target.value)}
          className="min-w-0 rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
        >
          {RESOURCE_TYPES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <p className="text-sm text-zinc-400 dark:text-zinc-500">Loading logs...</p>
      ) : isError ? (
        <p className="text-sm text-red-500">Failed to load audit logs.</p>
      ) : logs.length === 0 ? (
        <div className="rounded-lg border border-dashed border-zinc-300 p-4 text-center text-sm text-zinc-400 dark:border-zinc-700 dark:text-zinc-500">
          No audit logs yet
        </div>
      ) : (
        <ul className="flex max-h-56 flex-col gap-2 overflow-auto pr-1">
          {logs.slice(0, 8).map((log) => (
            <li key={log.audit_id}>
              <AuditLogCard log={log} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function AuditLogCard({ log }: { log: AuditLogResponse }) {
  return (
    <div className="rounded-md border border-zinc-200 p-2 text-sm dark:border-zinc-800">
      <div className="mb-1 flex items-center justify-between gap-2 text-xs">
        <span className="line-clamp-1 font-medium text-zinc-700 dark:text-zinc-300">
          {formatLabel(log.action)}
        </span>
        <span className="shrink-0 text-zinc-400">{formatTime(log.created_at)}</span>
      </div>
      <div className="flex items-center justify-between gap-2 text-[10px] text-zinc-400">
        <span>{formatLabel(log.resource_type)}</span>
        <span className="truncate">{log.actor_id}</span>
      </div>
      <p className="mt-1 truncate text-xs text-zinc-500 dark:text-zinc-400">
        {log.resource_id}
      </p>
      <p className="mt-1 line-clamp-2 text-[10px] text-zinc-400">
        {summarizeDetail(log)}
      </p>
    </div>
  );
}

function summarizeDetail(log: AuditLogResponse): string {
  const title = readString(log.detail_json.title);
  const status = readString(log.detail_json.status);
  const route = readString(log.detail_json.route);
  const answerStatus = readString(log.detail_json.answer_status);
  const parts = [title, status, route, answerStatus].filter(Boolean);
  return parts.length > 0 ? parts.join(" | ") : "No detail";
}

function readString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function formatLabel(value: string): string {
  return value.replaceAll("_", " ").replaceAll(".", " ");
}

function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleString(undefined, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
