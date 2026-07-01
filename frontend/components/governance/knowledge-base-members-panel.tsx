"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { KnowledgeBaseMemberRole } from "@/lib/types";

const ROLES: KnowledgeBaseMemberRole[] = ["viewer", "contributor", "manager", "owner"];

export function KnowledgeBaseMembersPanel({
  knowledgeBaseId,
}: {
  knowledgeBaseId: string | null;
}) {
  const queryClient = useQueryClient();
  const [userId, setUserId] = useState("");
  const [role, setRole] = useState<KnowledgeBaseMemberRole>("viewer");

  const membersQuery = useQuery({
    queryKey: ["knowledge-base-members", knowledgeBaseId],
    queryFn: () => apiClient.listKnowledgeBaseMembers(knowledgeBaseId ?? ""),
    enabled: Boolean(knowledgeBaseId),
    staleTime: 10_000,
  });

  const upsertMutation = useMutation({
    mutationFn: () =>
      apiClient.upsertKnowledgeBaseMember(knowledgeBaseId ?? "", userId.trim(), {
        role,
        status: "active",
      }),
    onSuccess: () => {
      setUserId("");
      queryClient.invalidateQueries({ queryKey: ["knowledge-base-members"] });
    },
  });

  const members = membersQuery.data?.members ?? [];

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          Members
        </h2>
        <button
          type="button"
          onClick={() => membersQuery.refetch()}
          disabled={!knowledgeBaseId || membersQuery.isFetching}
          className="text-xs font-medium text-zinc-500 underline-offset-2 hover:underline disabled:text-zinc-300 dark:text-zinc-400 dark:disabled:text-zinc-700"
        >
          {membersQuery.isFetching ? "Refreshing" : "Refresh"}
        </button>
      </div>

      <div className="grid grid-cols-[1fr_108px] gap-2 text-xs">
        <input
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
          placeholder="User ID"
          disabled={!knowledgeBaseId || upsertMutation.isPending}
          className="min-w-0 rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-600 placeholder:text-zinc-400 disabled:bg-zinc-100 disabled:text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:disabled:bg-zinc-900"
        />
        <select
          value={role}
          onChange={(event) => setRole(event.target.value as KnowledgeBaseMemberRole)}
          disabled={!knowledgeBaseId || upsertMutation.isPending}
          className="min-w-0 rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-600 disabled:bg-zinc-100 disabled:text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:disabled:bg-zinc-900"
        >
          {ROLES.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => upsertMutation.mutate()}
          disabled={!knowledgeBaseId || !userId.trim() || upsertMutation.isPending}
          className="col-span-2 rounded-md bg-zinc-900 px-2 py-1.5 text-xs font-medium text-white disabled:bg-zinc-200 disabled:text-zinc-400 dark:bg-zinc-100 dark:text-zinc-900 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-600"
        >
          {upsertMutation.isPending ? "Saving..." : "Save member"}
        </button>
      </div>

      {!knowledgeBaseId ? (
        <EmptyState text="Select a knowledge base." />
      ) : membersQuery.isLoading ? (
        <p className="text-sm text-zinc-400 dark:text-zinc-500">Loading members...</p>
      ) : membersQuery.isError ? (
        <p className="text-sm text-red-500">Failed to load members.</p>
      ) : members.length === 0 ? (
        <EmptyState text="No members yet" />
      ) : (
        <ul className="flex max-h-40 flex-col gap-1.5 overflow-auto pr-1">
          {members.map((member) => (
            <li
              key={member.membership_id}
              className="rounded-md border border-zinc-200 px-2 py-1.5 text-xs dark:border-zinc-800"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate font-medium text-zinc-700 dark:text-zinc-300">
                  {member.user_id}
                </span>
                <span className="shrink-0 text-zinc-400">{member.role}</span>
              </div>
              <p className="mt-0.5 text-[10px] text-zinc-400">{member.status}</p>
            </li>
          ))}
        </ul>
      )}

      {upsertMutation.isError && (
        <p className="text-xs text-red-500">Failed to save member.</p>
      )}
    </section>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-zinc-300 p-3 text-center text-sm text-zinc-400 dark:border-zinc-700 dark:text-zinc-500">
      {text}
    </div>
  );
}
