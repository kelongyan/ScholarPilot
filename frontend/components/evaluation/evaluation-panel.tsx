"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  EvaluationExecutionMode,
  EvaluationRunListFilters,
  EvaluationRunResponse,
} from "@/lib/types";

const MODES: Array<{ label: string; value: EvaluationExecutionMode }> = [
  { label: "Chat", value: "chat" },
  { label: "Agent", value: "agent" },
];

export function EvaluationPanel({
  knowledgeBaseId,
  onOpenChatTrace,
  onOpenAgentRun,
}: {
  knowledgeBaseId: string | null;
  onOpenChatTrace?: (traceId: string) => void;
  onOpenAgentRun?: (runId: string) => void;
}) {
  const queryClient = useQueryClient();
  const [datasetKey, setDatasetKey] = useState("phase2_fixed_qa");
  const [executionMode, setExecutionMode] = useState<EvaluationExecutionMode>("chat");
  const [selectedRun, setSelectedRun] = useState<EvaluationRunResponse | null>(null);

  const filters: EvaluationRunListFilters = useMemo(
    () => ({
      dataset_key: datasetKey,
      knowledge_base_id: knowledgeBaseId,
      execution_mode: executionMode,
    }),
    [datasetKey, executionMode, knowledgeBaseId]
  );

  const datasetsQuery = useQuery({
    queryKey: ["evaluation-datasets"],
    queryFn: () => apiClient.listEvaluationDatasets(),
    staleTime: 60_000,
  });

  const runsQuery = useQuery({
    queryKey: ["evaluation-runs", filters],
    queryFn: () => apiClient.listEvaluationRuns(filters),
    enabled: Boolean(knowledgeBaseId),
    staleTime: 10_000,
  });

  const runMutation = useMutation({
    mutationFn: () =>
      apiClient.createEvaluationRun({
        dataset_key: datasetKey,
        knowledge_base_id: knowledgeBaseId,
        execution_mode: executionMode,
        max_steps: 5,
      }),
    onSuccess: (run) => {
      setSelectedRun(run);
      queryClient.invalidateQueries({ queryKey: ["evaluation-runs"] });
    },
  });

  const datasets = datasetsQuery.data?.evaluation_datasets ?? [];
  const runs = runsQuery.data?.evaluation_runs ?? [];
  const latestRun = selectedRun ?? runs[0] ?? null;

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          Evaluations
        </h2>
        <button
          type="button"
          onClick={() => runsQuery.refetch()}
          disabled={!knowledgeBaseId || runsQuery.isFetching}
          className="text-xs font-medium text-zinc-500 underline-offset-2 hover:underline disabled:text-zinc-300 dark:text-zinc-400 dark:disabled:text-zinc-700"
        >
          {runsQuery.isFetching ? "Refreshing" : "Refresh"}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <select
          value={datasetKey}
          onChange={(event) => setDatasetKey(event.target.value)}
          className="col-span-2 min-w-0 rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
        >
          {datasets.length === 0 ? (
            <option value={datasetKey}>Phase 2 fixed QA</option>
          ) : (
            datasets.map((dataset) => (
              <option key={dataset.dataset_key} value={dataset.dataset_key}>
                {dataset.name}
              </option>
            ))
          )}
        </select>

        <select
          value={executionMode}
          onChange={(event) => setExecutionMode(event.target.value as EvaluationExecutionMode)}
          className="min-w-0 rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
        >
          {MODES.map((mode) => (
            <option key={mode.value} value={mode.value}>
              {mode.label}
            </option>
          ))}
        </select>

        <button
          type="button"
          disabled={!knowledgeBaseId || runMutation.isPending}
          onClick={() => runMutation.mutate()}
          className="rounded-md bg-zinc-900 px-2 py-1.5 text-xs font-medium text-white disabled:bg-zinc-200 disabled:text-zinc-400 dark:bg-zinc-100 dark:text-zinc-900 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-600"
        >
          {runMutation.isPending ? "Running..." : "Run"}
        </button>
      </div>

      {!knowledgeBaseId ? (
        <EmptyState text="Select a knowledge base to run evaluations." />
      ) : runsQuery.isLoading ? (
        <p className="text-sm text-zinc-400 dark:text-zinc-500">Loading runs...</p>
      ) : runsQuery.isError || datasetsQuery.isError ? (
        <p className="text-sm text-red-500">Failed to load evaluations.</p>
      ) : !latestRun ? (
        <EmptyState text="No evaluation runs yet" />
      ) : (
        <div className="flex flex-col gap-2">
          <RunSummary run={latestRun} />
          <ul className="flex max-h-48 flex-col gap-2 overflow-auto pr-1">
            {latestRun.items.slice(0, 5).map((item) => (
              <li
                key={item.item_id}
                className="rounded-md border border-zinc-200 p-2 text-sm dark:border-zinc-800"
              >
                <div className="mb-1 flex items-center justify-between gap-2 text-xs">
                  <span className="font-medium text-zinc-700 dark:text-zinc-300">
                    Q{item.sequence}
                  </span>
                  <span
                    className={
                      item.status === "passed" ? "text-green-600" : "text-red-500"
                    }
                  >
                    {item.status}
                  </span>
                </div>
                <p className="line-clamp-2 text-xs text-zinc-500 dark:text-zinc-400">
                  {item.question}
                </p>
                {item.missing_keywords.length > 0 && (
                  <p className="mt-1 line-clamp-1 text-[10px] text-red-500">
                    Missing: {item.missing_keywords.join(", ")}
                  </p>
                )}
                <div className="mt-2 flex items-center justify-between gap-2 text-[10px] text-zinc-400">
                  <span>
                    {item.answer_status} | {item.latency_ms}ms
                  </span>
                  <div className="flex shrink-0 items-center gap-2">
                    {item.chat_trace_id && onOpenChatTrace && (
                      <button
                        type="button"
                        onClick={() => onOpenChatTrace(item.chat_trace_id as string)}
                        className="font-medium text-zinc-500 underline-offset-2 hover:underline dark:text-zinc-400"
                      >
                        Trace
                      </button>
                    )}
                    {item.agent_run_id && onOpenAgentRun && (
                      <button
                        type="button"
                        onClick={() => onOpenAgentRun(item.agent_run_id as string)}
                        className="font-medium text-zinc-500 underline-offset-2 hover:underline dark:text-zinc-400"
                      >
                        Agent
                      </button>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function RunSummary({ run }: { run: EvaluationRunResponse }) {
  const averageKeywordCoverage = numberMetric(run.metrics_json.average_keyword_coverage);
  const averageRecallAtK = numberMetric(run.metrics_json.average_recall_at_k);
  const averageCitationAccuracy = numberMetric(
    run.metrics_json.average_citation_accuracy
  );
  const averageFaithfulness = numberMetric(run.metrics_json.average_faithfulness);
  const answerRate = numberMetric(run.metrics_json.answer_rate);
  const traceRate = numberMetric(run.metrics_json.trace_rate);
  const errorRate = numberMetric(run.metrics_json.error_rate);
  const passDelta = numberMetric(run.metric_deltas.pass_rate);
  const coverageDelta = numberMetric(run.metric_deltas.average_keyword_coverage);
  const recallDelta = numberMetric(run.metric_deltas.average_recall_at_k);
  const latencyDelta = numberMetric(run.metric_deltas.average_latency_ms);

  return (
    <div className="rounded-md border border-zinc-200 p-2 text-sm dark:border-zinc-800">
      <div className="mb-1 flex items-center justify-between gap-2 text-xs">
        <span className="font-medium text-zinc-700 dark:text-zinc-300">
          {run.execution_mode}
        </span>
        <span className="text-zinc-400">{formatTime(run.created_at)}</span>
      </div>
      <div className="grid grid-cols-3 gap-1 text-center text-xs">
        <Metric label="Pass" value={`${Math.round(run.pass_rate * 100)}%`} />
        <Metric label="Passed" value={String(run.passed_count)} />
        <Metric label="Failed" value={String(run.failed_count)} />
      </div>
      <div className="mt-1 grid grid-cols-4 gap-1 text-center text-xs">
        <Metric label="Coverage" value={`${Math.round(averageKeywordCoverage * 100)}%`} />
        <Metric label="Recall" value={`${Math.round(averageRecallAtK * 100)}%`} />
        <Metric label="Citation" value={`${Math.round(averageCitationAccuracy * 100)}%`} />
        <Metric label="Faith" value={`${Math.round(averageFaithfulness * 100)}%`} />
      </div>
      <div className="mt-1 grid grid-cols-4 gap-1 text-center text-xs">
        <Metric label="Answer" value={`${Math.round(answerRate * 100)}%`} />
        <Metric label="Trace" value={`${Math.round(traceRate * 100)}%`} />
        <Metric label="Error" value={`${Math.round(errorRate * 100)}%`} />
        <Metric label="Tokens" value={String(numberMetric(run.metrics_json.estimated_total_tokens))} />
      </div>
      <p className="mt-2 text-[10px] text-zinc-400">
        {run.question_count} questions | avg {run.average_latency_ms}ms |{" "}
        {shortVersion(run.dataset_version)}
      </p>
      {run.previous_run_id && (
        <p className="mt-1 text-[10px] text-zinc-400">
          vs previous: pass {formatDelta(passDelta, true)} | coverage{" "}
          {formatDelta(coverageDelta, true)} | recall {formatDelta(recallDelta, true)} |
          latency {formatDelta(latencyDelta, false)}ms
        </p>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-zinc-200 p-1 dark:border-zinc-800">
      <div className="font-medium text-zinc-700 dark:text-zinc-300">{value}</div>
      <div className="text-[10px] text-zinc-400">{label}</div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-zinc-300 p-4 text-center text-sm text-zinc-400 dark:border-zinc-700 dark:text-zinc-500">
      {text}
    </div>
  );
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

function numberMetric(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function formatDelta(value: number, asPercent: boolean): string {
  const rendered = asPercent ? `${Math.round(value * 100)}%` : String(Math.round(value));
  return value > 0 ? `+${rendered}` : rendered;
}

function shortVersion(value: string): string {
  return value ? value.replace("sha256:", "ds:") : "no snapshot";
}
