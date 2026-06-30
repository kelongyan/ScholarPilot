"use client";

import { useState } from "react";
import type {
  AgentRunResponse,
  AgentStepResponse,
  CitationResponse,
  DocumentResponse,
  KnowledgeBaseResponse,
  RetrievalTraceResponse,
} from "@/lib/types";
import { KnowledgeBasePanel } from "@/components/knowledge-base/knowledge-base-panel";
import { DocumentList } from "@/components/document/document-list";
import { ChatPanel } from "@/components/chat/chat-panel";
import { CitationPanel } from "@/components/citation/citation-panel";
import { AgentRunHistory } from "@/components/agent/agent-run-history";
import { KnowledgeOperationsPanel } from "@/components/knowledge-operations/knowledge-operations-panel";

/**
 * Kairos home page: three-column knowledge workspace.
 *
 * Left   - knowledge bases + source library
 * Center - evidence-grounded Q&A
 * Right  - citations, evidence, and retrieval trace for the latest answer
 */
export default function Home() {
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] =
    useState<KnowledgeBaseResponse | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<DocumentResponse | null>(null);
  const [citations, setCitations] = useState<CitationResponse[]>([]);
  const [trace, setTrace] = useState<RetrievalTraceResponse | null>(null);
  const [agentSteps, setAgentSteps] = useState<AgentStepResponse[]>([]);
  const [selectedAgentRunId, setSelectedAgentRunId] = useState<string | null>(null);

  const selectedKnowledgeBaseId = selectedKnowledgeBase?.knowledge_base_id ?? null;

  return (
    <div className="flex flex-col flex-1 bg-zinc-50 font-sans dark:bg-black">
      <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-3 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Kairos
          </span>
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
            Phase 5 | Controlled Agents
          </span>
        </div>
        <div className="text-sm text-zinc-500 dark:text-zinc-400">
          {selectedDoc ? (
            <span>
              {selectedDoc.title} | <span className="text-zinc-400">{selectedDoc.status}</span>
            </span>
          ) : selectedKnowledgeBase ? (
            <span>
              {selectedKnowledgeBase.name} | <span className="text-zinc-400">KB scope</span>
            </span>
          ) : (
            <span>No knowledge base selected</span>
          )}
        </div>
      </header>

      <div className="grid flex-1 grid-cols-1 md:grid-cols-[300px_1fr_360px]">
        <aside className="border-r border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
          <div className="flex flex-col gap-4">
            <KnowledgeBasePanel
              selectedKnowledgeBaseId={selectedKnowledgeBaseId}
              onSelect={(kb) => {
                setSelectedKnowledgeBase(kb);
                setSelectedDoc(null);
                setCitations([]);
                setTrace(null);
                setAgentSteps([]);
                setSelectedAgentRunId(null);
              }}
            />
            <DocumentList
              selectedDocId={selectedDoc?.doc_id ?? null}
              knowledgeBaseId={selectedKnowledgeBaseId}
              onClearSelection={() => {
                setSelectedDoc(null);
                setCitations([]);
                setTrace(null);
                setAgentSteps([]);
                setSelectedAgentRunId(null);
              }}
              onSelect={(doc) => {
                setSelectedDoc(doc);
                setCitations([]);
                setTrace(null);
                setAgentSteps([]);
                setSelectedAgentRunId(null);
              }}
            />
            <KnowledgeOperationsPanel knowledgeBaseId={selectedKnowledgeBaseId} />
          </div>
        </aside>

        <main className="flex flex-col border-r border-zinc-200 dark:border-zinc-800">
          <ChatPanel
            document={selectedDoc}
            knowledgeBaseId={selectedKnowledgeBaseId}
            onAnswerArtifacts={({
              citations: nextCitations,
              trace: nextTrace,
              agentSteps: nextAgentSteps,
              agentRunId: nextAgentRunId,
            }) => {
              setCitations(nextCitations);
              setTrace(nextTrace);
              setAgentSteps(nextAgentSteps ?? []);
              setSelectedAgentRunId(nextAgentRunId ?? null);
            }}
          />
        </main>

        <aside className="bg-white p-4 dark:bg-zinc-950">
          <div className="flex flex-col gap-4">
            <AgentRunHistory
              knowledgeBaseId={selectedKnowledgeBaseId}
              selectedRunId={selectedAgentRunId}
              onSelect={(run: AgentRunResponse) => {
                setSelectedAgentRunId(run.run_id);
                setCitations(run.citations);
                setTrace(run.trace ?? null);
                setAgentSteps(run.agent_steps);
              }}
            />
            <CitationPanel citations={citations} trace={trace} agentSteps={agentSteps} />
          </div>
        </aside>
      </div>
    </div>
  );
}
