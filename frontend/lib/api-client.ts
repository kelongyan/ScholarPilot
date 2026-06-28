/**
 * API client for the ScholarPilot backend.
 *
 * Phase 0: skeleton only. Phase 1 will add typed methods for documents,
 * search, chat, and citations.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiClient {
  constructor(private readonly baseUrl: string = API_BASE_URL) {}

  /** Check whether the backend is reachable. */
  async health(): Promise<{ status: string }> {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) {
      throw new Error(`Health check failed: ${res.status}`);
    }
    return res.json() as Promise<{ status: string }>;
  }
}

export const apiClient = new ApiClient();
