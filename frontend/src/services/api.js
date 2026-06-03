const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request(path, options) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new ApiError(res.status, text);
  }

  return res.json();
}

export const api = {
  calculateRisk: (data) =>
    request("/calculate", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  analyzeClinicalCase: (text, currentData = {}) =>
    request("/nlp/analyze", {
      method: "POST",
      body: JSON.stringify({ text, current_data: currentData }),
    }),

  health: () => request("/health"),
};
