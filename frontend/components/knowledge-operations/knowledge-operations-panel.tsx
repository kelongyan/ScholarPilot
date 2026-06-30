"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { KnowledgeOperationSuggestionResponse } from "@/lib/types";

const SEVERITY_STYLES: Record<string, string> = {
  high: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  medium: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  low: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
};

export function KnowledgeOperationsPanel({
  knowledgeBaseId,
}: {
  knowledgeBaseId: string | null;
}) {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["knowledge-operation-suggestions", knowledgeBaseId],
    queryFn: () => apiClient.listKnowledgeOperationSuggestions(knowledgeBaseId),
    staleTime: 10_000,
    enabled: Boolean(knowledgeBaseId),
  });

  const suggestions = data?.suggestions ?? [];

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Operations
          </h2>
          <p className="text-[11px] text-zinc-400">
            {suggestions.length} pending suggestion(s)
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

      {!knowledgeBaseId ? (
        <EmptyState text="Select a knowledge base to view operations." />
      ) : isLoading ? (
        <p className="text-sm text-zinc-400 dark:text-zinc-500">Loading...</p>
      ) : isError ? (
        <p className="text-sm text-red-500">Failed to load suggestions.</p>
      ) : suggestions.length === 0 ? (
        <EmptyState text="No pending suggestions" />
      ) : (
        <ul className="flex max-h-64 flex-col gap-2 overflow-auto pr-1">
          {suggestions.slice(0, 6).map((suggestion) => (
            <li key={suggestion.suggestion_id}>
              <SuggestionCard suggestion={suggestion} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function SuggestionCard({
  suggestion,
}: {
  suggestion: KnowledgeOperationSuggestionResponse;
}) {
  return (
    <div className="rounded-md border border-zinc-200 p-2 text-sm dark:border-zinc-800">
      <div className="mb-1 flex items-center justify-between gap-2">
        <span className="line-clamp-1 font-medium text-zinc-800 dark:text-zinc-100">
          {suggestion.title}
        </span>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${
            SEVERITY_STYLES[suggestion.severity] ?? SEVERITY_STYLES.low
          }`}
        >
          {suggestion.severity}
        </span>
      </div>
      <p className="line-clamp-2 text-xs text-zinc-500 dark:text-zinc-400">
        {suggestion.description}
      </p>
      <p className="mt-1 line-clamp-2 text-xs text-zinc-600 dark:text-zinc-300">
        {suggestion.suggested_action}
      </p>
      <div className="mt-2 flex items-center justify-between gap-2 text-[10px] text-zinc-400">
        <span>{formatSuggestionType(suggestion.suggestion_type)}</span>
        <span>{suggestion.status}</span>
      </div>
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

function formatSuggestionType(value: string): string {
  return value.replaceAll("_", " ");
}
