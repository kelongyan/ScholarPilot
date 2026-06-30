"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { KnowledgeBaseResponse } from "@/lib/types";

export function KnowledgeBasePanel({
  selectedKnowledgeBaseId,
  canManage,
  onSelect,
}: {
  selectedKnowledgeBaseId: string | null;
  canManage: boolean;
  onSelect: (kb: KnowledgeBaseResponse) => void;
}) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["knowledge-bases"],
    queryFn: () => apiClient.listKnowledgeBases(),
  });

  const mutation = useMutation({
    mutationFn: () =>
      apiClient.createKnowledgeBase({
        name: name.trim(),
        status: "active",
        visibility: "private",
      }),
    onSuccess: (kb) => {
      setName("");
      onSelect(kb);
      queryClient.invalidateQueries({ queryKey: ["knowledge-bases"] });
    },
  });

  const knowledgeBases = useMemo(() => data?.knowledge_bases ?? [], [data?.knowledge_bases]);
  const selected = useMemo(
    () =>
      knowledgeBases.find((kb) => kb.knowledge_base_id === selectedKnowledgeBaseId) ?? null,
    [knowledgeBases, selectedKnowledgeBaseId]
  );

  useEffect(() => {
    if (!selectedKnowledgeBaseId && knowledgeBases.length > 0) {
      onSelect(knowledgeBases[0]);
    }
  }, [knowledgeBases, onSelect, selectedKnowledgeBaseId]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          Knowledge Bases
        </h2>
        <span className="text-xs text-zinc-400">
          {selected ? selected.name : "none selected"}
        </span>
      </div>

      {isLoading && <p className="text-sm text-zinc-400">Loading...</p>}
      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">
          Backend not reachable. Is the API running on port 8000?
        </p>
      )}

      {canManage && (
        <div className="flex gap-2">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="New knowledge base"
            className="min-w-0 flex-1 rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
          />
          <button
            type="button"
            onClick={() => mutation.mutate()}
            disabled={!name.trim() || mutation.isPending}
            className="rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white disabled:bg-zinc-200 disabled:text-zinc-400 dark:bg-zinc-100 dark:text-zinc-900 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-600"
          >
            Create
          </button>
        </div>
      )}

      <ul className="flex flex-col gap-1.5">
        {knowledgeBases.map((kb) => (
          <li key={kb.knowledge_base_id}>
            <button
              type="button"
              onClick={() => onSelect(kb)}
              className={`w-full rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                selectedKnowledgeBaseId === kb.knowledge_base_id
                  ? "border-zinc-900 bg-zinc-100 dark:border-zinc-100 dark:bg-zinc-800"
                  : "border-zinc-200 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate font-medium text-zinc-900 dark:text-zinc-100">
                  {kb.name}
                </span>
                <span className="shrink-0 rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
                  {kb.status}
                </span>
              </div>
              {kb.description && (
                <p className="mt-1 line-clamp-2 text-xs text-zinc-400">
                  {kb.description}
                </p>
              )}
            </button>
          </li>
        ))}
        {!isLoading && knowledgeBases.length === 0 && !error && (
          <li className="rounded-lg border border-dashed border-zinc-300 p-4 text-center text-sm text-zinc-400 dark:border-zinc-700">
            No knowledge bases yet
          </li>
        )}
      </ul>
    </div>
  );
}
