import { useState } from "react";
import { AlertTriangle, FileDown, FileText, FlaskConical, Pill, Share2, ShieldAlert, Stethoscope, TriangleAlert } from "lucide-react";
import { gerarRelatorio } from "../../services/report";

const CORES_REC = {
  verde: { border: "var(--green)", bg: "var(--green-soft)" },
  amarelo: { border: "var(--amber)", bg: "var(--amber-soft)" },
  vermelho: { border: "var(--red)", bg: "var(--red-soft)" },
};

const HERO = {
  baixo: {
    bg: "var(--green-soft)",
    color: "var(--green)",
    border: "#A7D4BB",
    icon: (
      <svg width={32} height={32} viewBox="0 0 24 24" fill="none">
        <circle cx={12} cy={12} r={10} fill="#0E7B52" opacity={0.15} />
        <path d="M9 12l2 2 4-4" stroke="#0E7B52" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  intermediario: {
    bg: "var(--amber-soft)",
    color: "var(--amber)",
    border: "#FCD34D",
    icon: (
      <svg width={32} height={32} viewBox="0 0 24 24" fill="none">
        <path d="M12 3L2 21h20L12 3z" fill="#C47A00" opacity={0.15} />
        <path d="M12 9v4M12 17h.01" stroke="#C47A00" strokeWidth={2.2} strokeLinecap="round" />
      </svg>
    ),
  },
  alto: {
    bg: "var(--red-soft)",
    color: "var(--red)",
    border: "#F5B0AA",
    icon: (
      <svg width={32} height={32} viewBox="0 0 24 24" fill="none">
        <circle cx={12} cy={12} r={10} fill="#E03131" opacity={0.15} />
        <path d="M12 8v4M12 16h.01" stroke="#E03131" strokeWidth={2.2} strokeLinecap="round" />
      </svg>
    ),
  },
};

function SectionHeader({ label }) {
  return (
    <div
      style={{
        fontSize: 10,
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.1em",
        color: "var(--ink-muted)",
        padding: "0 2px",
      }}
    >
      {label}
    </div>
  );
}

function CollapsibleSection({ label, defaultOpen = true, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: "0 2px",
          textAlign: "left",
          fontFamily: "'Outfit', sans-serif",
        }}
      >
        <span
          style={{
            fontSize: 10,
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.1em",
            color: "var(--ink-muted)",
            flex: 1,
          }}
        >
          {label}
        </span>
        <span
          style={{
            fontSize: 10,
            color: "var(--ink-muted)",
            transition: "transform 0.2s",
            display: "inline-flex",
            transform: open ? "rotate(180deg)" : "none",
          }}
        >
          ▼
        </span>
      </button>
      {open && children}
    </div>
  );
}

async function handleShare(resultado, dados, nomeIndice) {
  const nome = dados.nome ? `Paciente: ${dados.nome}\n` : "";
  const text = [
    `CardioRisk Periop — Avaliação Cardiovascular Perioperatória`,
    ``,
    `${nome}Risco: ${resultado.rotulo_risco}`,
    `Score ${nomeIndice}: ${resultado.pontuacao} pt${resultado.pontuacao !== 1 ? "s" : ""}`,
    `Capacidade Funcional: ${resultado.mets} METs`,
    `Cirurgia: ${resultado.rotulo_cirurgia}`,
    `Risco do Procedimento: ${resultado.risco_cirurgia === "baixo" ? "Baixo" : resultado.risco_cirurgia === "alto" ? "Alto" : "Intermediário"}`,
    ``,
    resultado.recomendacoes.length > 0 ? `Recomendações:\n${resultado.recomendacoes.map((r) => `• ${r.titulo}: ${r.corpo}`).join("\n")}` : "",
    resultado.orientacoes_medicacao.length > 0 ? `\nManejo de Medicamentos:\n${resultado.orientacoes_medicacao.map((m) => `• ${m.medicamento}: ${m.acao} — ${m.detalhe}`).join("\n")}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  try {
    if (navigator.share) {
      await navigator.share({ title: "CardioRisk Periop", text });
    } else {
      await navigator.clipboard.writeText(text);
    }
  } catch {
    // Usuário cancelou ou clipboard não disponível
  }
}

export function EtapaResultado({ resultado, dados }) {
  const [copied, setCopied] = useState(false);
  const nomeIndice = resultado.indice_risco === "vsg" ? "VSG" : "RCRI";
  const hero = HERO[resultado.classe_risco] ?? HERO.baixo;

  const iconeRec = {
    verde: <Stethoscope size={18} strokeWidth={2.2} color="var(--green)" />,
    amarelo: <TriangleAlert size={18} strokeWidth={2.2} color="var(--amber)" />,
    vermelho: <ShieldAlert size={18} strokeWidth={2.2} color="var(--red)" />,
  };

  const onShare = async () => {
    await handleShare(resultado, dados, nomeIndice);
    if (!navigator.share) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <>
      {/* Alerta de condições ativas */}
      {resultado.tem_condicoes_ativas && (
        <div
          style={{
            background: "var(--red-soft)",
            border: "1px solid #F5B0AA",
            borderRadius: "var(--r)",
            padding: "14px 16px",
            display: "flex",
            gap: 12,
            alignItems: "flex-start",
          }}
        >
          <span style={{ display: "inline-flex", flexShrink: 0 }}>
            <AlertTriangle size={20} strokeWidth={2.2} color="var(--red)" />
          </span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--red)", marginBottom: 4 }}>
              Condições Cardíacas Ativas Detectadas
            </div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "var(--ink-mid)", lineHeight: 1.6 }}>
              {resultado.condicoes_ativas.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
            <div style={{ fontSize: 11, color: "var(--red)", marginTop: 6, fontWeight: 500 }}>
              Avaliar e tratar antes do procedimento cirúrgico.
            </div>
          </div>
        </div>
      )}

      {/* ── Card hero de risco ───────────────────────────────────────────── */}
      <div
        style={{
          borderRadius: "var(--r)",
          border: `1px solid ${hero.border}`,
          overflow: "hidden",
          boxShadow: "0 2px 8px rgba(13,17,23,0.08)",
        }}
      >
        {/* Área colorida hero */}
        <div
          style={{
            background: hero.bg,
            padding: "20px 20px 16px",
          }}
        >
          <div
            style={{
              fontSize: 10,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              fontWeight: 600,
              color: hero.color,
              opacity: 0.75,
              marginBottom: 10,
            }}
          >
            Estratificação de Risco ({nomeIndice})
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ display: "inline-flex", flexShrink: 0 }}>{hero.icon}</span>
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 34,
                fontWeight: 700,
                color: hero.color,
                lineHeight: 1,
              }}
            >
              {resultado.rotulo_risco}
            </span>
          </div>
        </div>

        {/* Grid de estatísticas */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            borderTop: `1px solid ${hero.border}`,
            background: "var(--white)",
          }}
        >
          {[
            { label: `Pontuação (${nomeIndice})`, value: `${resultado.pontuacao} pt${resultado.pontuacao !== 1 ? "s" : ""}` },
            { label: "Cap. Funcional", value: `${resultado.mets} METs` },
            { label: "Cirurgia", value: resultado.rotulo_cirurgia },
            {
              label: "Risco do Procedimento",
              value:
                resultado.risco_cirurgia === "baixo"
                  ? "Baixo"
                  : resultado.risco_cirurgia === "alto"
                  ? "Alto"
                  : "Intermediário",
            },
          ].map((cell, i) => (
            <div
              key={cell.label}
              style={{
                padding: "14px 16px",
                borderRight: i % 2 === 0 ? `1px solid ${hero.border}` : "none",
                borderBottom: i < 2 ? `1px solid ${hero.border}` : "none",
              }}
            >
              <div
                style={{
                  fontSize: 10,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: "var(--ink-muted)",
                  fontWeight: 600,
                  marginBottom: 4,
                }}
              >
                {cell.label}
              </div>
              <div
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 14,
                  fontWeight: 500,
                  color: "var(--ink)",
                  lineHeight: 1.3,
                }}
              >
                {cell.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Orientações de medicação ────────────────────────────────────────── */}
      {resultado.orientacoes_medicacao.length > 0 && (
        <CollapsibleSection label="Manejo de Medicamentos">
          {resultado.orientacoes_medicacao.map((med, i) => {
            const cores = CORES_REC[med.tipo] || CORES_REC.amarelo;
            return (
              <div
                key={i}
                style={{
                  background: "var(--white)",
                  borderRadius: "var(--r)",
                  border: "1px solid var(--border)",
                  borderLeft: `3px solid ${cores.border}`,
                  padding: "14px 16px",
                  boxShadow: "0 1px 4px rgba(13,17,23,0.06)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 4,
                  }}
                >
                  <span style={{ fontSize: 13, fontWeight: 700, color: "var(--ink)" }}>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                      <Pill size={14} strokeWidth={2.2} color="var(--ink-mid)" />
                      {med.medicamento}
                    </span>
                  </span>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      padding: "3px 8px",
                      borderRadius: 999,
                      background: cores.bg,
                      color: cores.border,
                    }}
                  >
                    {med.acao}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: "var(--ink-mid)", lineHeight: 1.55 }}>
                  {med.detalhe}
                </div>
              </div>
            );
          })}
        </CollapsibleSection>
      )}

      {/* ── Exames recomendados ────────────────────────────────────────── */}
      {resultado.exames_recomendados.length > 0 && (
        <CollapsibleSection label="Exames Recomendados">
          <div
            style={{
              background: "var(--white)",
              borderRadius: "var(--r)",
              border: "1px solid var(--border)",
              padding: 16,
              boxShadow: "0 1px 4px rgba(13,17,23,0.06)",
            }}
          >
            <div
              style={{
                fontSize: 11,
                color: "var(--amber)",
                background: "var(--amber-soft)",
                padding: "6px 10px",
                borderRadius: 6,
                marginBottom: 10,
                fontWeight: 500,
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <TriangleAlert size={13} strokeWidth={2.2} color="var(--amber)" />
              Realizar antes do procedimento cirúrgico
            </div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "var(--ink-mid)", lineHeight: 1.8 }}>
              {resultado.exames_recomendados.map((exame, i) => (
                <li key={i}>{exame}</li>
              ))}
            </ul>
          </div>
        </CollapsibleSection>
      )}

      {/* ── Recomendações ──────────────────────────────────────────── */}
      {resultado.recomendacoes.length > 0 && (
        <CollapsibleSection label="Recomendações" defaultOpen={true}>
          {resultado.recomendacoes.map((rec, i) => {
            const cores = CORES_REC[rec.tipo] || CORES_REC.verde;
            return (
              <div
                key={i}
                style={{
                  background: "var(--white)",
                  borderRadius: "var(--r)",
                  border: "1px solid var(--border)",
                  borderLeft: `3px solid ${cores.border}`,
                  padding: "14px 16px",
                  display: "flex",
                  gap: 12,
                  alignItems: "flex-start",
                  boxShadow: "0 1px 4px rgba(13,17,23,0.06)",
                }}
              >
                <span style={{ display: "inline-flex", flexShrink: 0 }}>
                  {iconeRec[rec.tipo] ?? iconeRec.verde}
                </span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 3, color: "var(--ink)" }}>
                    {rec.titulo}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--ink-mid)", lineHeight: 1.55 }}>
                    {rec.corpo}
                  </div>
                </div>
              </div>
            );
          })}
        </CollapsibleSection>
      )}

      {/* ── Fatores de risco ─────────────────────────────────────────────── */}
      {resultado.fatores_risco.length > 0 && (
        <CollapsibleSection label="Fatores Identificados" defaultOpen={false}>
          <div
            style={{
              background: "var(--white)",
              borderRadius: "var(--r)",
              border: "1px solid var(--border)",
              padding: 16,
              boxShadow: "0 1px 4px rgba(13,17,23,0.06)",
            }}
          >
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {resultado.fatores_risco.map((f, i) => (
                <span
                  key={i}
                  style={{
                    fontSize: 11,
                    padding: "4px 10px",
                    borderRadius: 999,
                    background: "var(--bg)",
                    border: "1px solid var(--border)",
                    color: "var(--ink-muted)",
                    fontWeight: 500,
                  }}
                >
                  {f}
                </span>
              ))}
            </div>
          </div>
        </CollapsibleSection>
      )}

      {/* ── Ações ──────────────────────────────────────────────────── */}
      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={onShare}
          style={{
            flex: "0 0 auto",
            padding: "14px 16px",
            background: "var(--white)",
            color: "var(--ink-mid)",
            border: "1.5px solid var(--border)",
            borderRadius: "var(--r)",
            fontSize: 13,
            fontWeight: 600,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 6,
            transition: "all 0.15s",
          }}
          title="Compartilhar resumo"
        >
          <span style={{ display: "inline-flex" }}>
            <Share2 size={16} strokeWidth={2.2} color={copied ? "var(--green)" : "var(--ink-mid)"} />
          </span>
          {copied ? "Copiado!" : "Compartilhar"}
        </button>

        <button
          onClick={() => gerarRelatorio(resultado, dados)}
          style={{
            flex: 1,
            padding: "14px 20px",
            background: "var(--blue)",
            color: "#fff",
            border: "none",
            borderRadius: "var(--r)",
            fontSize: 14,
            fontWeight: 600,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            boxShadow: "0 2px 8px rgba(15,76,129,0.25)",
          }}
        >
          <span style={{ display: "inline-flex" }}>
            <FileDown size={18} strokeWidth={2.2} color="#fff" />
          </span>
          Baixar PDF
        </button>
      </div>

      <p
        style={{
          textAlign: "center",
          fontSize: 10,
          color: "var(--ink-muted)",
          lineHeight: 1.7,
          padding: "0 8px",
        }}
      >
        Ferramenta de suporte clínico. Não substitui o julgamento médico individualizado.
        <br />
        Baseado na Diretriz Brasileira de Avaliação Cardiovascular Perioperatória, RCRI (Lee) e VSG.
      </p>
    </>
  );
}
