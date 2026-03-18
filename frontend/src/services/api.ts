import type { PatientData, RiskResult } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new ApiError(res.status, text);
  }

  return res.json() as Promise<T>;
}

export const api = {
  /**
   * Send patient data to the backend and receive the full risk assessment.
   */
  calculateRisk: (data: PatientData): Promise<RiskResult> =>
    request<RiskResult>("/calculate", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  /**
   * Health check — useful to verify backend connectivity on app load.
   */
  health: (): Promise<{ status: string }> =>
    request<{ status: string }>("/health"),

  /**
   * Send chat messages to the RAG-augmented assistant and receive a response.
   */
  chat: (messages: { role: string; content: string }[]): Promise<{ role: string; content: string }> =>
    request<{ role: string; content: string }>("/chat", {
      method: "POST",
      body: JSON.stringify({ messages }),
    }),

  /**
   * Extract clinical data from conversation history and compute the risk result,
   * ready for PDF generation via generateReport().
   */
  chatReport: (
    messages: { role: string; content: string }[],
  ): Promise<{ result: RiskResult; patient: { name?: string; age?: number } }> =>
    request<{ result: RiskResult; patient: { name?: string; age?: number } }>("/chat/report", {
      method: "POST",
      body: JSON.stringify({ messages }),
    }),
};
