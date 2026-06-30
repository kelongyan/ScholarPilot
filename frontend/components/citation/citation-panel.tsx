"use client";

import { useState } from "react";
import type {
  AgentStepResponse,
  CitationResponse,
  RetrievalTraceResponse,
} from "@/lib/types";

/**
 * Citation / evidence panel: shows answer sources, retrieval trace, and Agent steps.
 */
export function CitationPanel({
  citations,
  trace,
  agentSteps,
}: {
  citations: CitationResponse[];
  trace: RetrievalTraceResponse | null;
  agentSteps: AgentStepResponse[];
}) {
  const [showTrace, setShowTrace] = useState(false);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          Citations &amp; Evidence
        </h2>
        <button
          type="button"
          onClick={() => setShowTrace((prev) => !prev)}
          className="text-xs font-medium text-zinc-500 underline-offset-2 hover:underline dark:text-zinc-400"
        >
          {showTrace ? "Hide trace" : "Show trace"}
        </button>
      </div>

      {citations.length === 0 ? (
        <div className="rounded-lg border border-dashed border-zinc-300 p-6 text-center text-sm text-zinc-400 dark:border-zinc-700 dark:text-zinc-500">
          Answer sources will appear here
        </div>
      ) : (
        <ul className="flex flex-col gap-2">
          {citations.map((cite, i) => (
            <li
              key={cite.chunk_id}
              className="rounded-md border border-zinc-200 p-3 dark:border-zinc-800"
            >
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="font-medium text-zinc-700 dark:text-zinc-300">
                  [{i + 1}] Page {cite.page}
                </span>
                <span className="text-zinc-400">
                  score {cite.score.toFixed(3)}
                </span>
              </div>
              {cite.section && (
                <p className="mb-1 text-xs text-zinc-500">{cite.section}</p>
              )}
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                &quot;{cite.quote}&quot;
              </p>
            </li>
          ))}
        </ul>
      )}

      {agentSteps.length > 0 && (
        <div className="rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Agent Trace
          </h3>
          <ul className="flex flex-col gap-2">
            {agentSteps.map((step) => (
              <li
                key={`${step.agent_name}-${step.sequence}`}
                className="rounded border border-zinc-200 p-2 text-sm dark:border-zinc-800"
              >
                <div className="mb-1 flex items-center justify-between gap-2 text-xs">
                  <span className="font-medium text-zinc-700 dark:text-zinc-300">
                    {step.sequence}. {step.agent_name}
                  </span>
                  <span className="shrink-0 text-zinc-400">
                    {step.status} | {step.latency_ms}ms
                  </span>
                </div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  {formatStepSummary(step)}
                </p>
                {step.error_message && (
                  <p className="mt-1 text-xs text-red-500">{step.error_message}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {showTrace && (
        <div className="rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Retrieval Trace
          </h3>
          {!trace ? (
            <p className="text-sm text-zinc-400 dark:text-zinc-500">
              No retrieval trace available for this answer yet.
            </p>
          ) : (
            <div className="flex flex-col gap-3 text-sm text-zinc-600 dark:text-zinc-400">
              <div>
                <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                  Query
                </p>
                <p className="whitespace-pre-wrap">{trace.query}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                  Rewritten query
                </p>
                <p className="whitespace-pre-wrap">{trace.rewritten_query}</p>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="rounded border border-zinc-200 p-2 dark:border-zinc-800">
                  Dense results: {trace.dense_results.length}
                </div>
                <div className="rounded border border-zinc-200 p-2 dark:border-zinc-800">
                  Sparse results: {trace.sparse_results.length}
                </div>
                <div className="rounded border border-zinc-200 p-2 dark:border-zinc-800">
                  Fused results: {trace.fused_results.length}
                </div>
                <div className="rounded border border-zinc-200 p-2 dark:border-zinc-800">
                  Reranked: {trace.reranked_results.length}
                </div>
              </div>
              <div>
                <p className="mb-2 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                  Evidence Pack
                </p>
                {trace.evidence_pack.length === 0 ? (
                  <p className="text-xs text-zinc-400 dark:text-zinc-500">
                    No evidence pack items.
                  </p>
                ) : (
                  <ul className="flex flex-col gap-2">
                    {trace.evidence_pack.map((item, index) => (
                      <li
                        key={`${item.chunk_id}-${index}`}
                        className="rounded border border-zinc-200 p-2 dark:border-zinc-800"
                      >
                        <div className="mb-1 flex items-center justify-between text-xs">
                          <span>
                            [{index + 1}] p.{item.page_start}
                            {item.page_end > item.page_start ? `-${item.page_end}` : ""}
                          </span>
                          <span>{item.retrieval_source}</span>
                        </div>
                        {item.section && (
                          <p className="mb-1 text-xs text-zinc-500">{item.section}</p>
                        )}
                        <p className="line-clamp-4 whitespace-pre-wrap text-sm">
                          {item.text}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function formatStepSummary(step: AgentStepResponse): string {
  const output = step.output_json;
  if (typeof output.route === "string") {
    return `route: ${output.route}`;
  }
  if (typeof output.evidence_count === "number") {
    return `evidence: ${output.evidence_count}`;
  }
  if (typeof output.answer_status === "string") {
    return `answer: ${output.answer_status}`;
  }
  if (typeof output.review_status === "string") {
    return `review: ${output.review_status}`;
  }
  return step.status;
}
