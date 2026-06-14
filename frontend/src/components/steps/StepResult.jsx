import { useState } from "react";
import { AlertTriangle, FileDown, FileText, FlaskConical, Pill, Share2, ShieldAlert, Stethoscope, TriangleAlert } from "lucide-react";
import { generateReport } from "../../services/report";

const REC_COLORS = {
  green: { border: "var(--green)", bg: "var(--green-soft)" },
  amber: { border: "var(--amber)", bg: "var(--amber-soft)" },
  red: { border: "var(--red)", bg: "var(--red-soft)" },
};

const HERO = {
  low: {
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
  intermediate: {
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
  high: {
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

async function handleShare(result, data, indexName) {
  const name = data.name ? `Paciente: ${data.name}\n` : "";
  const text = [
    `CardioRisk Periop — Avaliação Cardiovascular Perioperatória`,
    ``,
    `${name}Risco: ${result.risk_label}`,
    `Score ${indexName}: ${result.score} pt${result.score !== 1 ? "s" : ""}`,
    `Capacidade Funcional: ${result.mets} METs`,
    `Cirurgia: ${result.surgery_label}`,
    `Risco do Procedimento: ${result.surgery_risk === "low" ? "Baixo" : result.surgery_risk === "high" ? "Alto" : "Intermediário"}`,
    ``,
    result.recommendations.length > 0 ? `Recomendações:\n${result.recommendations.map((r) => `• ${r.title}: ${r.body}`).join("\n")}` : "",
    result.medication_advice.length > 0 ? `\nManejo de Medicamentos:\n${result.medication_advice.map((m) => `• ${m.medication}: ${m.action} — ${m.detail}`).join("\n")}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  try {
    if (navigator.share) {
      await navigator.share({ title: "CardioRisk Periop", text });
    } else {
      await navigator.clipboard.writeText(text);
      // Brief visual feedback handled by button state
    }
  } catch {
    // User cancelled or clipboard not available
  }
}

export function EtapaResultado({ result, data }) {
  const [copied, setCopied] = useState(false);
  const indexName = result.risk_index === "vsg" ? "VSG" : "RCRI";
  const hero = HERO[result.risk_class] ?? HERO.low;

  const recIcon = {
    green: <Stethoscope size={18} strokeWidth={2.2} color="var(--green)" />,
    amber: <TriangleAlert size={18} strokeWidth={2.2} color="var(--amber)" />,
    red: <ShieldAlert size={18} strokeWidth={2.2} color="var(--red)" />,
  };

  const onShare = async () => {
    await handleShare(result, data, indexName);
    if (!navigator.share) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <>
      {/* Active conditions alert */}
      {result.has_active_conditions && (
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
              {result.active_conditions.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
            <div style={{ fontSize: 11, color: "var(--red)", marginTop: 6, fontWeight: 500 }}>
              Avaliar e tratar antes do procedimento cirúrgico.
            </div>
          </div>
        </div>
      )}

      {/* ── Hero risk card ───────────────────────────────────────────── */}
      <div
        style={{
          borderRadius: "var(--r)",
          border: `1px solid ${hero.border}`,
          overflow: "hidden",
          boxShadow: "0 2px 8px rgba(13,17,23,0.08)",
        }}
      >
        {/* Colored hero area */}
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
            Estratificação de Risco ({indexName})
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
              {result.risk_label}
            </span>
          </div>
        </div>

        {/* Stats grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            borderTop: `1px solid ${hero.border}`,
            background: "var(--white)",
          }}
        >
          {[
            { label: `Pontuação (${indexName})`, value: `${result.score} pt${result.score !== 1 ? "s" : ""}` },
            { label: "Cap. Funcional", value: `${result.mets} METs` },
            { label: "Cirurgia", value: result.surgery_label },
            {
              label: "Risco do Procedimento",
              value:
                result.surgery_risk === "low"
                  ? "Baixo"
                  : result.surgery_risk === "high"
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

      {/* ── Medication advice ────────────────────────────────────────── */}
      {result.medication_advice.length > 0 && (
        <CollapsibleSection label="Manejo de Medicamentos">
          {result.medication_advice.map((med, i) => {
            const colors = REC_COLORS[med.type] || REC_COLORS.amber;
            return (
              <div
                key={i}
                style={{
                  background: "var(--white)",
                  borderRadius: "var(--r)",
                  border: "1px solid var(--border)",
                  borderLeft: `3px solid ${colors.border}`,
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
                      {med.medication}
                    </span>
                  </span>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      padding: "3px 8px",
                      borderRadius: 999,
                      background: colors.bg,
                      color: colors.border,
                    }}
                  >
                    {med.action}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: "var(--ink-mid)", lineHeight: 1.55 }}>
                  {med.detail}
                </div>
              </div>
            );
          })}
        </CollapsibleSection>
      )}

      {/* ── Recommended exams ────────────────────────────────────────── */}
      {result.recommended_exams.length > 0 && (
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
              {result.recommended_exams.map((exam, i) => (
                <li key={i}>{exam}</li>
              ))}
            </ul>
          </div>
        </CollapsibleSection>
      )}

      {/* ── Recommendations ──────────────────────────────────────────── */}
      {result.recommendations.length > 0 && (
        <CollapsibleSection label="Recomendações" defaultOpen={true}>
          {result.recommendations.map((rec, i) => {
            const colors = REC_COLORS[rec.type] || REC_COLORS.green;
            return (
              <div
                key={i}
                style={{
                  background: "var(--white)",
                  borderRadius: "var(--r)",
                  border: "1px solid var(--border)",
                  borderLeft: `3px solid ${colors.border}`,
                  padding: "14px 16px",
                  display: "flex",
                  gap: 12,
                  alignItems: "flex-start",
                  boxShadow: "0 1px 4px rgba(13,17,23,0.06)",
                }}
              >
                <span style={{ display: "inline-flex", flexShrink: 0 }}>
                  {recIcon[rec.type] ?? recIcon.green}
                </span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 3, color: "var(--ink)" }}>
                    {rec.title}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--ink-mid)", lineHeight: 1.55 }}>
                    {rec.body}
                  </div>
                </div>
              </div>
            );
          })}
        </CollapsibleSection>
      )}

      {/* ── Risk factors ─────────────────────────────────────────────── */}
      {result.risk_factors.length > 0 && (
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
              {result.risk_factors.map((f, i) => (
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

      {/* ── Actions ──────────────────────────────────────────────────── */}
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
          onClick={() => generateReport(result, data)}
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
