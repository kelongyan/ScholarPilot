"use client";

import { useState } from "react";
import type { CitationResponse, DocumentResponse } from "@/lib/types";
import { DocumentList } from "@/components/document/document-list";
import { ChatPanel } from "@/components/chat/chat-panel";
import { CitationPanel } from "@/components/citation/citation-panel";

/**
 * ScholarPilot home page: three-column research workspace.
 *
 * Left   — document library (upload + list with live status)
 * Center — reader & chat (ask questions, see answers)
 * Right  — citations & evidence (source chunks for the latest answer)
 */
export default function Home() {
  const [selectedDoc, setSelectedDoc] = useState<DocumentResponse | null>(null);
  const [citations, setCitations] = useState<CitationResponse[]>([]);

  return (
    <div className="flex flex-col flex-1 bg-zinc-50 font-sans dark:bg-black">
      {/* Top bar */}
      <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-3 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            ScholarPilot
          </span>
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
            Phase 1 · RAG MVP
          </span>
        </div>
        <div className="text-sm text-zinc-500 dark:text-zinc-400">
          {selectedDoc ? (
            <span>
              {selectedDoc.title} ·{" "}
              <span className="text-zinc-400">{selectedDoc.status}</span>
            </span>
          ) : (
            <span>No document selected</span>
          )}
        </div>
      </header>

      {/* Three-column workspace */}
      <div className="grid flex-1 grid-cols-1 md:grid-cols-[280px_1fr_320px]">
        {/* Left: document library */}
        <aside className="border-r border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
          <DocumentList
            selectedDocId={selectedDoc?.doc_id ?? null}
            onSelect={(doc) => {
              setSelectedDoc(doc);
              setCitations([]);
            }}
          />
        </aside>

        {/* Center: reader + chat */}
        <main className="flex flex-col border-r border-zinc-200 dark:border-zinc-800">
          {selectedDoc ? (
            <ChatPanel
              document={selectedDoc}
              onCitations={setCitations}
            />
          ) : (
            <div className="flex flex-1 items-center justify-center p-6 text-center text-sm text-zinc-400">
              Select or upload a document to start asking questions.
            </div>
          )}
        </main>

        {/* Right: citation / evidence panel */}
        <aside className="bg-white p-4 dark:bg-zinc-950">
          <CitationPanel citations={citations} />
        </aside>
      </div>
    </div>
  );
}
