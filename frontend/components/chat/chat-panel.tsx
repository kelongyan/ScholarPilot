"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  AgentRunResponse,
  AgentStepResponse,
  ChatResponse,
  DocumentResponse,
  RetrievalTraceResponse,
} from "@/lib/types";

type AskMode = "chat" | "agent";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: ChatResponse["citations"];
  trace?: RetrievalTraceResponse | null;
  questionLogId?: string | null;
  agentRunId?: string | null;
  agentRoute?: string | null;
  agentSteps?: AgentStepResponse[];
}

/**
 * Chat panel: ask questions about the selected source and show grounded answers.
 * Citations and trace from the latest answer are shown in the right-hand panel.
 */
export function ChatPanel({
  document,
  knowledgeBaseId,
  onAnswerArtifacts,
}: {
  document: DocumentResponse | null;
  knowledgeBaseId: string | null;
  onAnswerArtifacts: (artifacts: {
    citations: ChatResponse["citations"];
    trace: RetrievalTraceResponse | null;
    agentSteps?: AgentStepResponse[];
  }) => void;
}) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [askMode, setAskMode] = useState<AskMode>("chat");
  const [feedbackMessageId, setFeedbackMessageId] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async ({
      question,
      mode,
    }: {
      question: string;
      mode: AskMode;
    }): Promise<
      | { kind: "chat"; data: ChatResponse }
      | { kind: "agent"; data: AgentRunResponse }
    > => {
      const request = {
        doc_id: document?.doc_id ?? null,
        knowledge_base_id: document ? null : knowledgeBaseId,
        question,
      };
      if (mode === "agent") {
        return {
          kind: "agent",
          data: await apiClient.runAgent({
            ...request,
            mode: "auto",
            max_steps: 5,
          }),
        };
      }
      return { kind: "chat", data: await apiClient.chat(request) };
    },
    onSuccess: (result, variables) => {
      const agentSteps = result.kind === "agent" ? result.data.agent_steps : [];
      setMessages((prev) => [
        ...prev,
        { role: "user", content: variables.question },
        {
          role: "assistant",
          content: result.data.answer,
          citations: result.data.citations,
          trace: result.data.trace ?? null,
          questionLogId: result.data.question_log_id ?? null,
          agentRunId: result.kind === "agent" ? result.data.run_id : null,
          agentRoute: result.kind === "agent" ? result.data.route : null,
          agentSteps,
        },
      ]);
      onAnswerArtifacts({
        citations: result.data.citations,
        trace: result.data.trace ?? null,
        agentSteps,
      });
    },
    onError: (err: Error, variables) => {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: variables.question },
        { role: "assistant", content: `Error: ${err.message}` },
      ]);
    },
  });

  const feedbackMutation = useMutation({
    mutationFn: ({
      questionLogId,
      useful,
      citationAccurate,
    }: {
      questionLogId: string;
      useful: boolean;
      citationAccurate: boolean;
    }) =>
      apiClient.submitFeedback(questionLogId, {
        useful,
        citation_accurate: citationAccurate,
      }),
    onSuccess: (_data, variables) => {
      setFeedbackMessageId(variables.questionLogId);
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || mutation.isPending) return;
    setInput("");
    mutation.mutate({ question, mode: askMode });
  }

  const ready = document ? document.status === "indexed" : Boolean(knowledgeBaseId);

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-auto p-4">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-center text-sm text-zinc-400">
            {ready
              ? document
                ? "Ask a question about this source."
                : "Ask a question about this knowledge base."
              : document
                ? `Source is ${document.status}. Please wait for indexing to complete.`
                : "Select a knowledge base to start asking questions."}
          </div>
        ) : (
          <ul className="flex flex-col gap-3">
            {messages.map((msg, i) => (
              <li
                key={i}
                className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                  msg.role === "user"
                    ? "self-end bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                    : "self-start bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
                {msg.citations && msg.citations.length > 0 && (
                  <p className="mt-1 text-xs opacity-70">
                    {msg.citations.length} citation(s)
                    {msg.trace ? " | trace ready" : ""}
                  </p>
                )}
                {msg.agentSteps && msg.agentSteps.length > 0 && (
                  <div className="mt-2 rounded-md border border-zinc-200 bg-white/60 p-2 text-xs text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900/50 dark:text-zinc-300">
                    <div className="mb-1 flex items-center justify-between">
                      <span>{msg.agentRoute ?? "agent"} route</span>
                      <span>{msg.agentSteps.length} steps</span>
                    </div>
                    <ul className="flex flex-col gap-1">
                      {msg.agentSteps.map((step) => (
                        <li
                          key={`${msg.agentRunId ?? "run"}-${step.sequence}`}
                          className="flex items-center justify-between gap-2"
                        >
                          <span className="truncate">{step.agent_name}</span>
                          <span className="shrink-0 text-zinc-400">
                            {step.status} | {step.latency_ms}ms
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {msg.role === "assistant" && msg.questionLogId && (
                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    <button
                      type="button"
                      disabled={feedbackMutation.isPending}
                      onClick={() => {
                        feedbackMutation.mutate({
                          questionLogId: msg.questionLogId!,
                          useful: true,
                          citationAccurate: true,
                        });
                      }}
                      className="rounded-md border border-zinc-300 px-2 py-1 text-zinc-600 hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
                    >
                      Useful
                    </button>
                    <button
                      type="button"
                      disabled={feedbackMutation.isPending}
                      onClick={() => {
                        feedbackMutation.mutate({
                          questionLogId: msg.questionLogId!,
                          useful: false,
                          citationAccurate: false,
                        });
                      }}
                      className="rounded-md border border-zinc-300 px-2 py-1 text-zinc-600 hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
                    >
                      Not useful
                    </button>
                    {feedbackMessageId === msg.questionLogId && !feedbackMutation.isPending && (
                      <span className="self-center text-zinc-400">Saved</span>
                    )}
                  </div>
                )}
              </li>
            ))}
            {mutation.isPending && (
              <li className="self-start rounded-lg bg-zinc-100 px-3 py-2 text-sm text-zinc-400 dark:bg-zinc-800">
                {askMode === "agent" ? "Running Agent..." : "Retrieving evidence..."}
              </li>
            )}
          </ul>
        )}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-zinc-200 p-3 dark:border-zinc-800">
        <div className="mb-2 inline-flex rounded-md border border-zinc-300 bg-white p-0.5 text-xs dark:border-zinc-700 dark:bg-zinc-900">
          {(["chat", "agent"] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setAskMode(mode)}
              className={`rounded px-3 py-1 font-medium ${
                askMode === mode
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
              }`}
            >
              {mode === "chat" ? "Chat" : "Agent"}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              ready
                ? document
                  ? "Ask a question about the source..."
                  : "Ask a question about this knowledge base..."
                : document
                  ? "Waiting for indexing..."
                  : "Select a knowledge base..."
            }
            disabled={!ready || mutation.isPending}
            className="flex-1 rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 disabled:bg-zinc-50 disabled:text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:disabled:bg-zinc-900/50"
          />
          <button
            type="submit"
            disabled={!ready || mutation.isPending || !input.trim()}
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:bg-zinc-200 disabled:text-zinc-400 dark:bg-zinc-100 dark:text-zinc-900 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-600"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
