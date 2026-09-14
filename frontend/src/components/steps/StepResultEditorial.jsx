import { useState } from "react";
import { AlertTriangle, FileDown, Share2 } from "lucide-react";
import { gerarRelatorio } from "../../services/report";
import { LinhaTempoMedicacoes } from "../MedicationTimeline";
import { CORES_REC, handleShare } from "./StepResult";
import { resumirCirurgia } from "../../utils/resumo";

const TOM_SCORE = {
  baixo: "var(--green)",
  intermediario: "var(--amber)",
  alto: "var(--red)",
};

function SecaoTitulo({ children }) {
  return (
    <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--ink-muted)", marginBottom: 14 }}>
      {children}
    </div>
  );
}

export function EtapaResultadoEditorial({ resultado, dados }) {
  const [copied, setCopied] = useState(false);
  const nomeIndice = resultado.indice_risco === "vsg" ? "VSG-CRI" : "RCRI";
  const corScore = TOM_SCORE[resultado.classe_risco] ?? TOM_SCORE.baixo;
  const dataGerado = new Date().toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" });
  const rotuloCirurgia = resumirCirurgia(dados).rotulo || "Não informada";

  const onShare = async () => {
    await handleShare(resultado, dados, nomeIndice);
    if (!navigator.share) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const rotuloRiscoCirurgia =
    resultado.risco_cirurgia === "baixo" ? "Baixo" : resultado.risco_cirurgia === "alto" ? "Alto" : "Intermediário";

  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: "36px 8px 60px" }}>
      {/* ── Masthead ─────────────────────────────────────────────────── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 20, paddingBottom: 20, borderBottom: "1px solid var(--border)", marginBottom: 24, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--blue)", marginBottom: 8 }}>
            Avaliação de Risco Cardiovascular Perioperatório
          </div>
          <h1 style={{ fontSize: 25, fontWeight: 700, letterSpacing: "-0.01em" }}>{dados.nome?.trim() || "Paciente não identificado"}</h1>
          <div style={{ fontSize: 12.5, color: "var(--ink-muted)", marginTop: 6, fontFamily: "'JetBrains Mono', monospace" }}>
            {dados.idade != null ? `${dados.idade} anos` : "idade não informada"} · {rotuloCirurgia} · risco {rotuloRiscoCirurgia.toLowerCase()} · gerado {dataGerado}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
          <button
            type="button"
            onClick={onShare}
            style={{
              padding: "9px 16px", borderRadius: 999, border: "1px solid var(--border)", background: "var(--white)",
              fontFamily: "'Outfit', sans-serif", fontSize: 12, fontWeight: 600, cursor: "pointer", color: "var(--ink-mid)",
              display: "flex", alignItems: "center", gap: 6,
            }}
          >
            <Share2 size={14} strokeWidth={2.2} color={copied ? "var(--green)" : "var(--ink-mid)"} />
            {copied ? "Copiado!" : "Compartilhar"}
          </button>
          <button
            type="button"
            onClick={() => gerarRelatorio(resultado, dados)}
            style={{
              padding: "9px 18px", borderRadius: 999, border: "none", background: "var(--blue)", color: "#fff",
              fontFamily: "'Outfit', sans-serif", fontSize: 12, fontWeight: 600, cursor: "pointer",
              display: "flex", alignItems: "center", gap: 6,
            }}
          >
            <FileDown size={15} strokeWidth={2.2} />
            Baixar PDF
          </button>
        </div>
      </div>

      {/* ── Condições ativas ─────────────────────────────────────────── */}
      {resultado.tem_condicoes_ativas && (
        <div style={{ background: "var(--red-soft)", border: "1px solid var(--red-border)", borderRadius: "var(--r)", padding: "14px 16px", display: "flex", gap: 12, alignItems: "flex-start", marginBottom: 24 }}>
          <AlertTriangle size={20} strokeWidth={2.2} color="var(--red)" style={{ flexShrink: 0 }} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--red)", marginBottom: 4 }}>Condições Cardíacas Ativas Detectadas</div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "var(--ink-mid)", lineHeight: 1.6 }}>
              {resultado.condicoes_ativas.map((c, i) => <li key={i}>{c}</li>)}
            </ul>
          </div>
        </div>
      )}

      {/* ── Score ─────────────────────────────────────────────────────── */}
      <div style={{ display: "flex", alignItems: "baseline", gap: 20, paddingBottom: 24, marginBottom: 26, borderBottom: "1px solid var(--border)", flexWrap: "wrap" }}>
        <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 44, fontWeight: 700, lineHeight: 1, color: corScore }}>
          {resultado.pontuacao}
          <span style={{ fontSize: 18, opacity: 0.55 }}> pt{resultado.pontuacao !== 1 ? "s" : ""}</span>
        </div>
        <div style={{ maxWidth: "60ch" }}>
          <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 3, color: corScore }}>
            {resultado.rotulo_risco} — Índice {nomeIndice}
          </div>
          <div style={{ fontSize: 12.5, color: "var(--ink-mid)", lineHeight: 1.6 }}>
            Cirurgia: {rotuloCirurgia} · Risco do procedimento: {rotuloRiscoCirurgia} · Capacidade funcional: {resultado.mets} METs ({resultado.rotulo_mets})
          </div>
        </div>
      </div>

      {/* ── Timeline (largura total) ──────────────────────────────────── */}
      {resultado.orientacoes_medicacao.length > 0 && (
        <div style={{ marginBottom: 30 }}>
          <SecaoTitulo>Manejo de Medicamentos</SecaoTitulo>
          <LinhaTempoMedicacoes orientacoes={resultado.orientacoes_medicacao} />
        </div>
      )}

      {/* ── Duas colunas ──────────────────────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 48 }}>
        <div>
          {resultado.exames_recomendados.length > 0 && (
            <div style={{ marginBottom: 28 }}>
              <SecaoTitulo>Exames Recomendados</SecaoTitulo>
              {resultado.exames_recomendados.map((exame, i) => (
                <div key={i} style={{ display: "flex", gap: 12, padding: "10px 0", borderTop: i > 0 ? "1px solid var(--border)" : "none", fontSize: 12.5, color: "var(--ink-mid)" }}>
                  {exame}
                </div>
              ))}
            </div>
          )}
          {resultado.fatores_risco.length > 0 && (
            <div>
              <SecaoTitulo>Fatores Identificados</SecaoTitulo>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 7 }}>
                {resultado.fatores_risco.map((f, i) => (
                  <span key={i} style={{ fontSize: 11, padding: "4px 10px", borderRadius: 999, background: "var(--bg)", border: "1px solid var(--border)", color: "var(--ink-muted)", fontWeight: 500 }}>
                    {f}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        <div>
          {resultado.recomendacoes.length > 0 && (
            <div>
              <SecaoTitulo>Recomendações</SecaoTitulo>
              {resultado.recomendacoes.map((rec, i) => {
                const cores = CORES_REC[rec.tipo] || CORES_REC.verde;
                return (
                  <div key={i} style={{ borderLeft: `3px solid ${cores.border}`, paddingLeft: 12, paddingTop: i > 0 ? 12 : 0, paddingBottom: 12, marginBottom: 0 }}>
                    <div style={{ fontSize: 12.5, fontWeight: 700, marginBottom: 2 }}>{rec.titulo}</div>
                    <div style={{ fontSize: 11.5, color: "var(--ink-mid)", lineHeight: 1.55 }}>{rec.corpo}</div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <p style={{ textAlign: "center", fontSize: 10.5, color: "var(--ink-muted)", lineHeight: 1.7, marginTop: 40 }}>
        Ferramenta de suporte clínico. Não substitui o julgamento médico individualizado.
        <br />
        Baseado na Diretriz Brasileira de Avaliação Cardiovascular Perioperatória, RCRI (Lee) e VSG.
      </p>
    </div>
  );
}
