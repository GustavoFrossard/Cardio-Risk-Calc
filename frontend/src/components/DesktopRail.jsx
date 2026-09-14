import { FileDown } from "lucide-react";
import { ETAPAS_WIZARD } from "../types";
import { resumirPaciente, resumirCirurgia, ROTULO_RISCO_CIRURGIA } from "../utils/resumo";
import { Eyebrow } from "./ui";
import { gerarRelatorio } from "../services/report";

function AlternadorTema({ theme, onToggle }) {
  const isDark = theme === "dark";
  return (
    <button
      type="button"
      onClick={onToggle}
      title={isDark ? "Mudar para modo claro" : "Mudar para modo escuro"}
      aria-label={isDark ? "Mudar para modo claro" : "Mudar para modo escuro"}
      style={{
        width: 30, height: 30, borderRadius: 999, border: "1px solid var(--border)", background: "var(--white)",
        color: "var(--ink-mid)", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer",
        flexShrink: 0, padding: 0,
      }}
    >
      {isDark ? (
        <svg width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <circle cx={12} cy={12} r={4} />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
        </svg>
      ) : (
        <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      )}
    </button>
  );
}

function LinhaResumo({ rotulo, valor }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 8, fontSize: 11.5, padding: "5px 0", borderTop: "1px solid var(--border)" }}>
      <span style={{ color: "var(--ink-muted)" }}>{rotulo}</span>
      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 600, color: "var(--ink)", textAlign: "right" }}>{valor}</span>
    </div>
  );
}

export function PainelLateral({
  etapaAtual,
  maiorEtapa,
  totalEtapas,
  onIrParaEtapa,
  dados,
  resultado,
  theme,
  onToggleTheme,
  carregando,
  onVoltar,
  onAvancar,
  onReiniciar,
}) {
  const paciente = resumirPaciente(dados);
  const cirurgia = resumirCirurgia(dados);
  const isResult = etapaAtual === totalEtapas;
  const isLastInput = etapaAtual === totalEtapas - 1;

  const nextLabel = carregando ? "Calculando..." : isResult ? "Nova Avaliação" : isLastInput ? "Calcular Risco" : "Próximo →";

  return (
    <aside
      style={{
        width: 258,
        flexShrink: 0,
        background: "var(--bg-soft)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        padding: "20px 16px",
        height: "100vh",
        position: "sticky",
        top: 0,
        overflowY: "auto",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 24 }}>
        <div style={{ width: 30, height: 30, background: "var(--blue)", borderRadius: 9, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <svg width={16} height={16} viewBox="0 0 24 24" fill="none">
            <path d="M12 21C12 21 3 15.5 3 9C3 6.24 5.24 4 8 4C9.64 4 11.09 4.79 12 6.01C12.91 4.79 14.36 4 16 4C18.76 4 21 6.24 21 9C21 15.5 12 21 12 21Z" fill="white" />
          </svg>
        </div>
        <div style={{ fontSize: 13, fontWeight: 700, flex: 1 }}>CardioRisk Periop</div>
        <AlternadorTema theme={theme} onToggle={onToggleTheme} />
      </div>

      <nav style={{ display: "flex", flexDirection: "column", marginBottom: 22, position: "relative" }}>
        {ETAPAS_WIZARD.map((s, i) => {
          const done = s.id < etapaAtual;
          const current = s.id === etapaAtual;
          const clickable = done && onIrParaEtapa;
          return (
            <div key={s.id} style={{ position: "relative" }}>
              {i < ETAPAS_WIZARD.length - 1 && (
                <div style={{ position: "absolute", left: 15, top: 30, width: 1.5, height: 20, background: "var(--border)" }} />
              )}
              <div
                onClick={clickable ? () => onIrParaEtapa(s.id) : undefined}
                title={s.titulo}
                style={{
                  display: "flex", alignItems: "center", gap: 10, padding: "8px 6px", borderRadius: "var(--r-sm)",
                  cursor: clickable ? "pointer" : "default",
                  background: current ? "var(--white)" : "transparent",
                  boxShadow: current ? "0 1px 3px rgba(13,17,23,0.06)" : "none",
                }}
              >
                <div
                  style={{
                    width: 20, height: 20, borderRadius: "50%", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 10, fontWeight: 700, fontFamily: "'JetBrains Mono', monospace", zIndex: 1,
                    background: done ? "var(--green)" : current ? "var(--blue)" : "var(--white)",
                    border: !done && !current ? "1.5px solid var(--border)" : "none",
                    color: done || current ? "#fff" : "var(--ink-muted)",
                  }}
                >
                  {done ? "✓" : s.id}
                </div>
                <div style={{ fontSize: 12.5, fontWeight: 600, color: current ? "var(--ink)" : "var(--ink-mid)" }}>{s.titulo}</div>
              </div>
            </div>
          );
        })}
      </nav>

      <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ background: "var(--white)", border: "1px solid var(--border)", borderRadius: "var(--r-sm)", padding: 12 }}>
          <Eyebrow style={{ padding: 0, marginBottom: 7 }}>Paciente</Eyebrow>
          <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 2 }}>{dados.nome?.trim() || "Não informado"}</div>
          <div style={{ fontSize: 11, color: "var(--ink-muted)", marginBottom: 8 }}>
            {paciente.idade != null ? `${paciente.idade} anos` : "Idade não informada"}
            {cirurgia.definida ? ` · ${cirurgia.rotulo}` : ""}
          </div>
          {isResult && resultado ? (
            <>
              <LinhaResumo rotulo="Índice" valor={resultado.indice_risco === "vsg" ? "VSG-CRI" : "RCRI"} />
              <LinhaResumo rotulo="Pontuação" valor={`${resultado.pontuacao} pt${resultado.pontuacao !== 1 ? "s" : ""}`} />
              <LinhaResumo rotulo="METs" valor={resultado.mets} />
              <LinhaResumo rotulo="Risco cirúrgico" valor={ROTULO_RISCO_CIRURGIA[resultado.risco_cirurgia] || "—"} />
            </>
          ) : (
            <>
              <LinhaResumo rotulo="Cap. funcional" valor={paciente.mets != null ? `${paciente.mets} METs` : "—"} />
              <LinhaResumo rotulo="Risco cirúrgico" valor={cirurgia.definida ? ROTULO_RISCO_CIRURGIA[cirurgia.risco] || "—" : "—"} />
            </>
          )}
        </div>

        {isResult && resultado ? (
          <button
            type="button"
            onClick={() => gerarRelatorio(resultado, dados)}
            style={{
              width: "100%", padding: 11, borderRadius: "var(--r-sm)", border: "none", background: "var(--blue)", color: "#fff",
              fontFamily: "'Outfit', sans-serif", fontSize: 12.5, fontWeight: 600, cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center", gap: 7,
            }}
          >
            <FileDown size={15} strokeWidth={2.2} />
            Baixar PDF
          </button>
        ) : (
          <div style={{ display: "flex", gap: 8 }}>
            {etapaAtual > 1 && (
              <button
                type="button"
                onClick={onVoltar}
                style={{
                  flex: "0 0 auto", padding: "11px 14px", borderRadius: "var(--r-sm)", border: "1.5px solid var(--border)",
                  background: "var(--white)", color: "var(--ink-mid)", fontFamily: "'Outfit', sans-serif", fontSize: 12.5, fontWeight: 600, cursor: "pointer",
                }}
              >
                ← Voltar
              </button>
            )}
            <button
              type="button"
              onClick={onAvancar}
              disabled={carregando}
              style={{
                flex: 1, padding: 11, borderRadius: "var(--r-sm)", border: "none", background: "var(--blue)", color: "#fff",
                fontFamily: "'Outfit', sans-serif", fontSize: 12.5, fontWeight: 600, cursor: carregando ? "not-allowed" : "pointer", opacity: carregando ? 0.7 : 1,
              }}
            >
              {nextLabel}
            </button>
          </div>
        )}
        {isResult && (
          <button
            type="button"
            onClick={onReiniciar}
            style={{
              width: "100%", padding: 10, borderRadius: "var(--r-sm)", border: "1.5px solid var(--border)", background: "var(--white)",
              color: "var(--ink-mid)", fontFamily: "'Outfit', sans-serif", fontSize: 12.5, fontWeight: 600, cursor: "pointer",
            }}
          >
            Nova Avaliação
          </button>
        )}
      </div>
    </aside>
  );
}
