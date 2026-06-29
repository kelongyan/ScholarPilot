"use client";

import type { CitationResponse } from "@/lib/types";

/**
 * Citation / evidence panel: shows the source chunks supporting the latest
 * answer, with page numbers, scores, and quoted original text.
 */
export function CitationPanel({
  citations,
}: {
  citations: CitationResponse[];
}) {
  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
        Citations &amp; Evidence
      </h2>

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
                “{cite.quote}”
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
