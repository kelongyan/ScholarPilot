"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { DocumentResponse, DocumentStatus } from "@/lib/types";
import { UploadPanel } from "./upload-panel";

const STATUS_STYLES: Record<DocumentStatus, string> = {
  uploaded: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
  parsing: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400",
  parsed: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400",
  indexing: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400",
  indexed: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400",
  failed: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400",
};

/**
 * Source library: upload + list with live status polling.
 * Sources still processing (parsing/indexing) are polled every 2s.
 */
export function DocumentList({
  selectedDocId,
  knowledgeBaseId,
  canManage,
  onClearSelection,
  onSelect,
}: {
  selectedDocId: string | null;
  knowledgeBaseId: string | null;
  canManage: boolean;
  onClearSelection: () => void;
  onSelect: (doc: DocumentResponse) => void;
}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["documents", knowledgeBaseId],
    queryFn: () => apiClient.listDocuments(knowledgeBaseId),
    refetchInterval: (query) => {
      const docs = query.state.data?.documents ?? [];
      const inProgress = docs.some((d) =>
        ["uploaded", "parsing", "parsed", "indexing"].includes(d.status)
      );
      return inProgress ? 2000 : false;
    },
  });

  const documents = data?.documents ?? [];

  return (
    <div className="flex flex-col gap-3">
      {canManage && <UploadPanel knowledgeBaseId={knowledgeBaseId} />}

      <div className="flex items-center justify-between gap-2">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          Sources
        </h2>
        <button
          type="button"
          onClick={onClearSelection}
          className="text-[10px] text-zinc-400 underline-offset-2 hover:underline"
        >
          {knowledgeBaseId ? "KB scope" : "all sources"}
        </button>
      </div>

      {isLoading && <p className="text-sm text-zinc-400">Loading...</p>}
      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">
          Backend not reachable. Is the API running on port 8000?
        </p>
      )}

      <ul className="flex flex-col gap-1.5">
        {documents.map((doc) => (
          <li key={doc.doc_id}>
            <button
              type="button"
              onClick={() => onSelect(doc)}
              className={`w-full rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                selectedDocId === doc.doc_id
                  ? "border-zinc-900 bg-zinc-100 dark:border-zinc-100 dark:bg-zinc-800"
                  : "border-zinc-200 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate font-medium text-zinc-900 dark:text-zinc-100">
                  {doc.title}
                </span>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${STATUS_STYLES[doc.status]}`}
                >
                  {doc.status}
                </span>
              </div>
              {doc.page_count > 0 && (
                <span className="text-xs text-zinc-400">
                  {doc.page_count} pages
                </span>
              )}
            </button>
          </li>
        ))}
        {!isLoading && documents.length === 0 && !error && (
          <li className="rounded-lg border border-dashed border-zinc-300 p-4 text-center text-sm text-zinc-400 dark:border-zinc-700">
            No sources yet
          </li>
        )}
      </ul>
    </div>
  );
}
