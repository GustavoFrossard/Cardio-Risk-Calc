const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ErroApi extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
    this.name = "ErroApi";
  }
}

async function request(path, options) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Erro desconhecido");
    throw new ErroApi(res.status, text);
  }

  return res.json();
}

export const api = {
  calcularRisco: (dados) =>
    request("/calculate", {
      method: "POST",
      body: JSON.stringify(dados),
    }),

  analisarCasoClinico: (text, currentData = {}) =>
    request("/nlp/analyze", {
      method: "POST",
      body: JSON.stringify({ text, current_data: currentData }),
    }),

  verificarSaude: () => request("/health"),
};
