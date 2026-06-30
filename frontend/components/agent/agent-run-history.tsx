"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { AgentRunListFilters, AgentRunResponse } from "@/lib/types";

const ROUTES = [
  { label: "All routes", value: "" },
  { label: "Short", value: "short" },
  { label: "Multi-agent", value: "multi_agent" },
];

const STATUSES = [
  { label: "All statuses", value: "" },
  { label: "Completed", value: "completed" },
  { label: "Failed", value: "failed" },
  { label: "Max steps", value: "max_steps_exceeded" },
];

const ANSWER_STATUSES = [
  { label: "All answers", value: "" },
  { label: "Answered", value: "answered" },
  { label: "Insufficient evidence", value: "insufficient_evidence" },
  { label: "Failed", value: "failed" },
  { label: "Max steps", value: "max_steps_exceeded" },
];

export function AgentRunHistory({
  knowledgeBaseId,
  selectedRunId,
  onSelect,
}: {
  knowledgeBaseId: string | null;
  selectedRunId: string | null;
  onSelect: (run: AgentRunResponse) => void;
}) {
  const [scopeToCurrentKb, setScopeToCurrentKb] = useState(true);
  const [route, setRoute] = useState("");
  const [status, setStatus] = useState("");
  const [answerStatus, setAnswerStatus] = useState("");
  const [createdFrom, setCreatedFrom] = useState("");
  const [createdTo, setCreatedTo] = useState("");

  const filters: AgentRunListFilters = useMemo(
    () => ({
      knowledge_base_id: scopeToCurrentKb ? knowledgeBaseId : null,
      route,
      status,
      answer_status: answerStatus,
      created_from: toStartOfDay(createdFrom),
      created_to: toEndOfDay(createdTo),
    }),
    [answerStatus, createdFrom, createdTo, knowledgeBaseId, route, scopeToCurrentKb, status]
  );

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["agent-runs", filters],
    queryFn: () => apiClient.listAgentRuns(filters),
    staleTime: 10_000,
  });

  const runs = data?.agent_runs ?? [];

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          Agent Runs
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
          value={route}
          onChange={(event) => setRoute(event.target.value)}
          className="min-w-0 rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
        >
          {ROUTES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <select
          value={status}
          onChange={(event) => setStatus(event.target.value)}
          className="min-w-0 rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
        >
          {STATUSES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <select
          value={answerStatus}
          onChange={(event) => setAnswerStatus(event.target.value)}
          className="col-span-2 min-w-0 rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
        >
          {ANSWER_STATUSES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <input
          type="date"
          value={createdFrom}
          onChange={(event) => setCreatedFrom(event.target.value)}
          className="min-w-0 rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
        />
        <input
          type="date"
          value={createdTo}
          onChange={(event) => setCreatedTo(event.target.value)}
          className="min-w-0 rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
        />
      </div>

      {isLoading ? (
        <p className="text-sm text-zinc-400 dark:text-zinc-500">Loading runs...</p>
      ) : isError ? (
        <p className="text-sm text-red-500">Failed to load Agent runs.</p>
      ) : runs.length === 0 ? (
        <div className="rounded-lg border border-dashed border-zinc-300 p-4 text-center text-sm text-zinc-400 dark:border-zinc-700 dark:text-zinc-500">
          No Agent runs yet
        </div>
      ) : (
        <ul className="flex max-h-64 flex-col gap-2 overflow-auto pr-1">
          {runs.slice(0, 8).map((run) => (
            <li key={run.run_id}>
              <button
                type="button"
                onClick={() => onSelect(run)}
                className={`w-full rounded-md border p-2 text-left transition ${
                  selectedRunId === run.run_id
                    ? "border-zinc-900 bg-zinc-100 dark:border-zinc-100 dark:bg-zinc-800"
                    : "border-zinc-200 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
                }`}
              >
                <div className="mb-1 flex items-center justify-between gap-2 text-xs">
                  <span className="font-medium text-zinc-700 dark:text-zinc-300">
                    {run.route}
                  </span>
                  <span className="shrink-0 text-zinc-400">
                    {run.status} | {run.total_latency_ms}ms
                  </span>
                </div>
                <p className="line-clamp-2 text-sm text-zinc-600 dark:text-zinc-400">
                  {run.question}
                </p>
                <div className="mt-1 flex items-center justify-between text-xs text-zinc-400">
                  <span>{run.agent_steps.length} steps</span>
                  <span>{run.citations.length} citations</span>
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function toStartOfDay(value: string): string | null {
  return value ? `${value}T00:00:00` : null;
}

function toEndOfDay(value: string): string | null {
  return value ? `${value}T23:59:59` : null;
}
