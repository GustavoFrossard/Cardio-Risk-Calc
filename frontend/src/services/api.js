const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ErroApi extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
    this.name = "ErroApi";
  }
}

function extrairMensagemErro(body) {
  const detail = body?.detail;
  if (!detail) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item?.msg).filter(Boolean).join(" ") || null;
  }
  return null;
}

async function request(path, options) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = extrairMensagemErro(body) ?? `Erro ${res.status} ao comunicar com o servidor.`;
    throw new ErroApi(res.status, message);
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
