"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { ChatResponse, DocumentResponse } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: ChatResponse["citations"];
}

/**
 * Chat panel: ask questions about the selected document and show answers.
 * Citations from the latest answer are shown in the right-hand panel.
 */
export function ChatPanel({
  document,
  onCitations,
}: {
  document: DocumentResponse;
  onCitations: (citations: ChatResponse["citations"]) => void;
}) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);

  const mutation = useMutation({
    mutationFn: (question: string) =>
      apiClient.chat({ doc_id: document.doc_id, question }),
    onSuccess: (data: ChatResponse, question: string) => {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: question },
        { role: "assistant", content: data.answer, citations: data.citations },
      ]);
      onCitations(data.citations);
    },
    onError: (err: Error, question: string) => {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: question },
        { role: "assistant", content: `Error: ${err.message}` },
      ]);
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || mutation.isPending) return;
    setInput("");
    mutation.mutate(question);
  }

  const ready = document.status === "indexed";

  return (
    <div className="flex h-full flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-auto p-4">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-center text-sm text-zinc-400">
            {ready
              ? "Ask a question about this paper."
              : `Document is ${document.status}. Please wait for indexing to complete.`}
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
                  </p>
                )}
              </li>
            ))}
            {mutation.isPending && (
              <li className="self-start rounded-lg bg-zinc-100 px-3 py-2 text-sm text-zinc-400 dark:bg-zinc-800">
                Thinking…
              </li>
            )}
          </ul>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t border-zinc-200 p-3 dark:border-zinc-800">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              ready ? "Ask a question about the paper…" : "Waiting for indexing…"
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
