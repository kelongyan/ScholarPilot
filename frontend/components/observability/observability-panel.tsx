"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { ObservabilitySummaryResponse } from "@/lib/types";

export function ObservabilityPanel({
  knowledgeBaseId,
}: {
  knowledgeBaseId: string | null;
}) {
  const { data, isLoading, isError, isFetching, refetch } = useQuery({
    queryKey: ["observability-summary", knowledgeBaseId],
    queryFn: () => apiClient.getObservabilitySummary(knowledgeBaseId),
    enabled: Boolean(knowledgeBaseId),
    staleTime: 10_000,
  });

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          Observability
        </h2>
        <button
          type="button"
          onClick={() => refetch()}
          disabled={!knowledgeBaseId || isFetching}
          className="text-xs font-medium text-zinc-500 underline-offset-2 hover:underline disabled:text-zinc-300 dark:text-zinc-400 dark:disabled:text-zinc-700"
        >
          {isFetching ? "Refreshing" : "Refresh"}
        </button>
      </div>

      {!knowledgeBaseId ? (
        <EmptyState text="Select a knowledge base to view quality signals." />
      ) : isLoading ? (
        <p className="text-sm text-zinc-400 dark:text-zinc-500">Loading summary...</p>
      ) : isError || !data ? (
        <p className="text-sm text-red-500">Failed to load observability summary.</p>
      ) : (
        <Summary summary={data} />
      )}
    </section>
  );
}

function Summary({ summary }: { summary: ObservabilitySummaryResponse }) {
  const latest = summary.latest_evaluation;

  return (
    <div className="rounded-md border border-zinc-200 p-2 text-sm dark:border-zinc-800">
      <div className="grid grid-cols-3 gap-1 text-center text-xs">
        <Metric
          label="Pass"
          value={latest ? formatPercent(latest.pass_rate) : "n/a"}
        />
        <Metric label="No answer" value={formatPercent(summary.no_answer_rate)} />
        <Metric
          label="Backlog"
          value={String(summary.pending_operation_count)}
        />
      </div>
      <div className="mt-1 grid grid-cols-3 gap-1 text-center text-xs">
        <Metric
          label="Coverage"
          value={
            latest ? formatPercent(latest.average_keyword_coverage) : "n/a"
          }
        />
        <Metric
          label="Recall"
          value={latest ? formatPercent(latest.average_recall_at_k) : "n/a"}
        />
        <Metric
          label="Citation"
          value={
            latest ? formatPercent(latest.average_citation_accuracy) : "n/a"
          }
        />
      </div>
      <div className="mt-1 grid grid-cols-3 gap-1 text-center text-xs">
        <Metric
          label="Faith"
          value={latest ? formatPercent(latest.average_faithfulness) : "n/a"}
        />
        <Metric
          label="Feedback"
          value={formatPercent(summary.negative_feedback_rate)}
        />
        <Metric
          label="Latency"
          value={`${summary.average_trace_latency_ms}ms`}
        />
      </div>
      <div className="mt-2 flex flex-col gap-1 text-[10px] text-zinc-400">
        <p>
          Questions {summary.question_count} | answered {summary.answered_count} |
          traces {summary.trace_count}
        </p>
        <p>
          Pending signals {summary.operation_signal_count} | high severity{" "}
          {summary.high_severity_pending_count}
        </p>
        {latest && (
          <p>
            Latest eval {latest.execution_mode} | {formatTime(latest.created_at)}
          </p>
        )}
      </div>
      {summary.regression_alerts.length > 0 && (
        <ul className="mt-2 flex flex-col gap-1 text-[10px] text-red-500">
          {summary.regression_alerts.slice(0, 3).map((alert) => (
            <li key={`${alert.metric}-${alert.delta}`}>
              {alert.metric}: {formatSigned(alert.delta)}
            </li>
          ))}
        </ul>
      )}
      {summary.evaluation_trend.length > 0 && (
        <div className="mt-2 border-t border-zinc-200 pt-2 dark:border-zinc-800">
          <div className="mb-1 flex items-center justify-between text-[10px] text-zinc-400">
            <span>Trend</span>
            <span>{summary.evaluation_trend.length} runs</span>
          </div>
          <ul className="flex flex-col gap-1 text-[10px] text-zinc-500 dark:text-zinc-400">
            {summary.evaluation_trend.slice(-3).map((point) => (
              <li
                key={point.run_id}
                className="flex items-center justify-between gap-2"
              >
                <span>{formatTime(point.created_at)}</span>
                <span>
                  pass {formatPercent(point.pass_rate)} | recall{" "}
                  {formatPercent(point.average_recall_at_k)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {summary.latency_buckets.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1 text-[10px] text-zinc-400">
          {summary.latency_buckets.map((bucket) => (
            <span
              key={bucket.label}
              className="rounded border border-zinc-200 px-1.5 py-0.5 dark:border-zinc-800"
            >
              {bucket.label}: {bucket.count}
            </span>
          ))}
        </div>
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

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
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

function formatSigned(value: number): string {
  return value > 0 ? `+${value}` : String(value);
}
