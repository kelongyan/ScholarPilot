/**
 * ScholarPilot home page.
 *
 * Phase 0: static three-column layout skeleton. No API calls yet.
 * Phase 1 will wire up document upload, chat, and the citation panel.
 */

export default function Home() {
  return (
    <div className="flex flex-col flex-1 bg-zinc-50 font-sans dark:bg-black">
      {/* Top bar: project switch / search / status */}
      <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-3 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            ScholarPilot
          </span>
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
            Phase 0 · Skeleton
          </span>
        </div>
        <div className="flex items-center gap-4 text-sm text-zinc-500 dark:text-zinc-400">
          <span>Backend: not connected</span>
          <span className="h-4 w-px bg-zinc-200 dark:bg-zinc-800" />
          <span>Model: not configured</span>
        </div>
      </header>

      {/* Three-column workspace */}
      <div className="grid flex-1 grid-cols-1 md:grid-cols-[280px_1fr_320px]">
        {/* Left: document library */}
        <aside className="border-r border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Documents
          </h2>
          <div className="rounded-lg border border-dashed border-zinc-300 p-6 text-center text-sm text-zinc-400 dark:border-zinc-700 dark:text-zinc-500">
            No documents yet
          </div>
          <button
            type="button"
            disabled
            className="mt-3 w-full rounded-md bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-400 dark:bg-zinc-800 dark:text-zinc-500"
          >
            Upload PDF
          </button>
        </aside>

        {/* Center: reader + chat */}
        <main className="flex flex-col border-r border-zinc-200 dark:border-zinc-800">
          <section className="flex-1 overflow-auto p-6">
            <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-zinc-300 text-center text-sm text-zinc-400 dark:border-zinc-700 dark:text-zinc-500">
              PDF reader &amp; chat area
              <br />
              (Phase 1)
            </div>
          </section>
          <section className="border-t border-zinc-200 p-4 dark:border-zinc-800">
            <div className="flex items-center gap-2">
              <input
                type="text"
                disabled
                placeholder="Ask a question about the paper…"
                className="flex-1 rounded-md border border-zinc-300 bg-zinc-50 px-3 py-2 text-sm text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-600"
              />
              <button
                type="button"
                disabled
                className="rounded-md bg-zinc-200 px-4 py-2 text-sm font-medium text-zinc-400 dark:bg-zinc-800 dark:text-zinc-500"
              >
                Send
              </button>
            </div>
          </section>
        </main>

        {/* Right: citation / evidence panel */}
        <aside className="bg-white p-4 dark:bg-zinc-950">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Citations &amp; Evidence
          </h2>
          <div className="rounded-lg border border-dashed border-zinc-300 p-6 text-center text-sm text-zinc-400 dark:border-zinc-700 dark:text-zinc-500">
            Answer sources will appear here
          </div>
        </aside>
      </div>
    </div>
  );
}
