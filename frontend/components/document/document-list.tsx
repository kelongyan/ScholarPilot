"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
  const queryClient = useQueryClient();
  const [actionError, setActionError] = useState<string | null>(null);
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

  const refreshDocuments = () => {
    queryClient.invalidateQueries({ queryKey: ["documents"] });
  };

  const replaceMutation = useMutation({
    mutationFn: ({ docId, file }: { docId: string; file: File }) =>
      apiClient.replaceDocument(docId, file),
    onSuccess: (doc) => {
      setActionError(null);
      refreshDocuments();
      onSelect(doc);
    },
    onError: (err: Error) => setActionError(err.message),
  });

  const archiveMutation = useMutation({
    mutationFn: (docId: string) => apiClient.archiveDocument(docId),
    onSuccess: (doc) => {
      setActionError(null);
      refreshDocuments();
      if (selectedDocId === doc.doc_id) {
        onClearSelection();
      }
    },
    onError: (err: Error) => setActionError(err.message),
  });

  const restoreMutation = useMutation({
    mutationFn: (docId: string) => apiClient.restoreDocument(docId),
    onSuccess: (doc) => {
      setActionError(null);
      refreshDocuments();
      onSelect(doc);
    },
    onError: (err: Error) => setActionError(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (docId: string) => apiClient.deleteDocument(docId),
    onSuccess: (doc) => {
      setActionError(null);
      refreshDocuments();
      if (selectedDocId === doc.doc_id) {
        onClearSelection();
      }
    },
    onError: (err: Error) => setActionError(err.message),
  });

  const lifecycleActionPending =
    replaceMutation.isPending ||
    archiveMutation.isPending ||
    restoreMutation.isPending ||
    deleteMutation.isPending;

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
      {actionError && (
        <p className="text-xs text-red-600 dark:text-red-400">{actionError}</p>
      )}

      <ul className="flex flex-col gap-1.5">
        {documents.map((doc) => (
          <li
            key={doc.doc_id}
            className={`rounded-md border px-3 py-2 text-sm transition-colors ${
              selectedDocId === doc.doc_id
                ? "border-zinc-900 bg-zinc-100 dark:border-zinc-100 dark:bg-zinc-800"
                : "border-zinc-200 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
            }`}
          >
            <button
              type="button"
              onClick={() => onSelect(doc)}
              className="w-full text-left"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate font-medium text-zinc-900 dark:text-zinc-100">
                  {doc.title}
                </span>
                <div className="flex shrink-0 items-center gap-1">
                  {doc.lifecycle_status !== "active" && (
                    <span className="rounded-full bg-zinc-200 px-2 py-0.5 text-[10px] font-medium text-zinc-600 dark:bg-zinc-700 dark:text-zinc-300">
                      {doc.lifecycle_status}
                    </span>
                  )}
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${STATUS_STYLES[doc.status]}`}
                  >
                    {doc.status}
                  </span>
                </div>
              </div>
              <span className="text-xs text-zinc-400">
                {doc.source} | v{doc.version}
                {doc.page_count > 0 ? ` | ${doc.page_count} pages` : ""}
              </span>
            </button>
            {canManage && (
              <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[10px]">
                {doc.lifecycle_status === "active" && (
                  <>
                    <label className="cursor-pointer rounded border border-zinc-300 px-2 py-1 text-zinc-500 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800">
                      Replace
                      <input
                        type="file"
                        className="hidden"
                        accept=".pdf,.md,.markdown,.txt,.html,.htm,.docx,application/pdf,text/markdown,text/plain,text/html"
                        disabled={lifecycleActionPending}
                        onChange={(event) => {
                          const file = event.target.files?.[0];
                          if (file) {
                            replaceMutation.mutate({ docId: doc.doc_id, file });
                            event.target.value = "";
                          }
                        }}
                      />
                    </label>
                    <button
                      type="button"
                      onClick={() => archiveMutation.mutate(doc.doc_id)}
                      disabled={lifecycleActionPending}
                      className="rounded border border-zinc-300 px-2 py-1 text-zinc-500 hover:bg-zinc-100 disabled:text-zinc-300 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800"
                    >
                      Archive
                    </button>
                  </>
                )}
                {doc.lifecycle_status === "archived" && (
                  <button
                    type="button"
                    onClick={() => restoreMutation.mutate(doc.doc_id)}
                    disabled={lifecycleActionPending}
                    className="rounded border border-zinc-300 px-2 py-1 text-zinc-500 hover:bg-zinc-100 disabled:text-zinc-300 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800"
                  >
                    Restore
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => deleteMutation.mutate(doc.doc_id)}
                  disabled={lifecycleActionPending}
                  className="rounded border border-red-200 px-2 py-1 text-red-500 hover:bg-red-50 disabled:text-red-200 dark:border-red-900/70 dark:hover:bg-red-950/30"
                >
                  Delete
                </button>
              </div>
            )}
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
