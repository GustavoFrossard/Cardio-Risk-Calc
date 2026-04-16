import { useState, useRef, useEffect } from "react";
import { api, ApiError } from "../services/api";
import { generateReport } from "../services/report";
import type { PatientData } from "../types";

interface Message {
  id: number;
  role: "user" | "assistant" | "report_ready";
  text: string;
}

/** Returns true when the assistant text contains a completed risk calculation. */
function hasCalculationResult(text: string): boolean {
  const t = text.toLowerCase();
  // Must mention a recognised index
  const hasIndex =
    t.includes("rcri") ||
    t.includes("vsg-cri") ||
    t.includes("vsg cri");
  // Must also contain score/risk signals
  const hasScore =
    /\d+\s*(ponto|pont|pt)/.test(t) ||
    /\d+[,.]\d+\s*%/.test(t) ||
    /\d+\s*%/.test(t) ||
    t.includes("risco baixo") ||
    t.includes("risco intermediário") ||
    t.includes("risco alto") ||
    t.includes("classe i") ||
    t.includes("mace");
  return hasIndex && hasScore;
}

interface Props {
  onBack: () => void;
}

export function ChatPage({ onBack }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    { id: 0, role: "assistant", text: "Olá! Sou o assistente CardioRisk, especializado em avaliação de risco cardiovascular perioperatório baseado na Diretriz SBC 2024. Como posso ajudá-lo? 🫀" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { id: Date.now(), role: "user", text };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput("");
    setLoading(true);

    try {
      // Send conversation history (skip initial greeting for cleaner context)
      const history = updatedMessages
        .filter((m) => m.id !== 0)
        .map((m) => ({ role: m.role, content: m.text }));

      const response = await api.chat(history);
      const assistantMsg: Message = { id: Date.now() + 1, role: "assistant", text: response.content };
      setMessages((prev) => {
        const next = [...prev, assistantMsg];
        if (hasCalculationResult(response.content)) {
          next.push({ id: Date.now() + 2, role: "report_ready", text: "" });
        }
        return next;
      });
    } catch (err: unknown) {
      const detail =
        err instanceof ApiError
          ? `HTTP ${err.status}: ${err.message}`
          : err instanceof Error
            ? err.message
            : "Erro desconhecido";
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          text: `⚠️ Erro ao se comunicar com o assistente: ${detail}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (reportLoading) return;
    setReportLoading(true);
    try {
      const history = messages
        .filter((m) => m.id !== 0 && m.role !== "report_ready")
        .map((m) => ({ role: m.role as "user" | "assistant", content: m.text }));

      const { result, patient } = await api.chatReport(history);

      const patientData = {
        name: patient.name ?? undefined,
        age: patient.age ?? undefined,
      } as PatientData;

      generateReport(result, patientData);
    } catch (err: unknown) {
      const detail = err instanceof Error ? err.message : "Erro ao gerar relatório.";
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          role: "assistant",
          text: `⚠️ Não foi possível gerar o relatório: ${detail}`,
        },
      ]);
    } finally {
      setReportLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "var(--bg)" }}>
      {/* Header */}
      <div
        style={{
          background: "var(--white)",
          padding: "52px 16px 12px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          gap: 12,
          position: "sticky",
          top: 0,
          zIndex: 50,
        }}
      >
        <button
          onClick={onBack}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: 4,
            display: "flex",
            alignItems: "center",
            color: "var(--blue)",
          }}
        >
          <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <div
          style={{
            width: 32,
            height: 32,
            background: "var(--blue)",
            borderRadius: 10,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: 16 }}>🤖</span>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--ink)" }}>Assistente CardioRisk</div>
          <div style={{ fontSize: 11, color: "var(--ink-muted)" }}>{loading ? "Digitando..." : "Online"}</div>
        </div>
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: loading ? "#FCD34D" : "#34D399",
            boxShadow: "0 0 0 2px var(--white)",
          }}
        />
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px 16px 8px", display: "flex", flexDirection: "column", gap: 10 }}>
        {messages.map((msg) => {
          if (msg.role === "report_ready") {
            return (
              <div key={msg.id} style={{ display: "flex", justifyContent: "flex-start" }}>
                <div
                  style={{
                    maxWidth: "80%",
                    padding: "12px 14px",
                    borderRadius: "14px 14px 14px 4px",
                    background: "#EFF6FF",
                    border: "1px solid #BFDBFE",
                    boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ fontSize: 15 }}>📄</span>
                    <span style={{ fontSize: 13, fontWeight: 600, color: "#1E40AF" }}>
                      Relatório disponível para download
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: 12, color: "#3B82F6", lineHeight: 1.4 }}>
                    Com base no cálculo acima, posso gerar o relatório PDF completo — idêntico ao da calculadora.
                  </p>
                  <button
                    onClick={handleGenerateReport}
                    disabled={reportLoading}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 6,
                      padding: "8px 14px",
                      borderRadius: 8,
                      border: "none",
                      background: reportLoading ? "#93C5FD" : "#1D4ED8",
                      color: "#fff",
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: reportLoading ? "not-allowed" : "pointer",
                      alignSelf: "flex-start",
                    }}
                  >
                    <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    {reportLoading ? "Gerando PDF..." : "Baixar Relatório PDF"}
                  </button>
                </div>
              </div>
            );
          }
          return (
            <div
              key={msg.id}
              style={{
                display: "flex",
                justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
              }}
            >
              <div
                style={{
                  maxWidth: "80%",
                  padding: "10px 14px",
                  borderRadius: msg.role === "user" ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
                  background: msg.role === "user" ? "var(--blue)" : "var(--white)",
                  color: msg.role === "user" ? "#fff" : "var(--ink)",
                  fontSize: 13,
                  lineHeight: 1.5,
                  border: msg.role === "assistant" ? "1px solid var(--border)" : "none",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
                  whiteSpace: "pre-wrap",
                }}
              >
                {msg.text}
              </div>
            </div>
          );
        })}
        {loading && (
          <div style={{ display: "flex", justifyContent: "flex-start" }}>
            <div
              style={{
                padding: "10px 14px",
                borderRadius: "14px 14px 14px 4px",
                background: "var(--white)",
                border: "1px solid var(--border)",
                fontSize: 13,
                color: "var(--ink-muted)",
              }}
            >
              Pensando...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div
        style={{
          padding: "12px 16px",
          paddingBottom: "max(12px, env(safe-area-inset-bottom))",
          background: "var(--white)",
          borderTop: "1px solid var(--border)",
          display: "flex",
          gap: 8,
          alignItems: "center",
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder={loading ? "Aguardando resposta..." : "Digite sua dúvida..."}
          disabled={loading}
          style={{
            flex: 1,
            padding: "10px 14px",
            borderRadius: 12,
            border: "1px solid var(--border)",
            background: "var(--bg)",
            fontSize: 13,
            color: "var(--ink)",
            outline: "none",
          }}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          style={{
            width: 38,
            height: 38,
            borderRadius: 12,
            background: input.trim() && !loading ? "var(--blue)" : "var(--bg)",
            border: input.trim() && !loading ? "none" : "1px solid var(--border)",
            cursor: input.trim() && !loading ? "pointer" : "default",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            transition: "all 0.2s",
          }}
        >
          <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke={input.trim() && !loading ? "#fff" : "var(--ink-muted)"} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 2L11 13" />
            <path d="M22 2L15 22L11 13L2 9L22 2Z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
