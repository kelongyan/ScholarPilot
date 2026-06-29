"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

/**
 * PDF upload panel. Uploads a file and triggers async processing on the
 * backend, then invalidates the document list.
 */
export function UploadPanel() {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (file: File) => apiClient.uploadDocument(file),
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      mutation.mutate(file);
      e.target.value = "";
    }
  }

  return (
    <div>
      <label
        className={`block w-full cursor-pointer rounded-md px-3 py-2 text-center text-sm font-medium transition-colors ${
          mutation.isPending
            ? "bg-zinc-200 text-zinc-400 dark:bg-zinc-800 dark:text-zinc-500"
            : "bg-zinc-900 text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        }`}
      >
        {mutation.isPending ? "Uploading…" : "Upload PDF"}
        <input
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={handleFile}
          disabled={mutation.isPending}
        />
      </label>
      {error && (
        <p className="mt-2 text-xs text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  );
}
