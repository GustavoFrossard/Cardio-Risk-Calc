import { generateReport } from "../../services/report";

const REC_COLORS = {
  green: { border: "var(--green)", bg: "var(--green-soft)" },
  amber: { border: "var(--amber)", bg: "var(--amber-soft)" },
  red: { border: "var(--red)", bg: "var(--red-soft)" },
};

const PILL_COLORS = {
  low: { bg: "var(--green-soft)", color: "var(--green)" },
  intermediate: { bg: "var(--amber-soft)", color: "var(--amber)" },
  high: { bg: "var(--red-soft)", color: "var(--red)" },
};

export function EtapaResultado({ result, data }) {
  const pill = PILL_COLORS[result.risk_class] ?? PILL_COLORS.low;
  const indexName = result.risk_index === "vsg" ? "VSG" : "RCRI";

  return (
    <>
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
          <span style={{ fontSize: 20, flexShrink: 0 }}>🚨</span>
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

      <div
        style={{
          background: "var(--white)",
          borderRadius: "var(--r)",
          border: "1px solid var(--border)",
          overflow: "hidden",
          boxShadow: "0 1px 4px rgba(13,17,23,0.06)",
        }}
      >
        <div style={{ padding: "20px 20px 0" }}>
          <div style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 600, color: "var(--ink-muted)", marginBottom: 6 }}>
            Estratificação de Risco ({indexName})
          </div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 8, marginBottom: 8 }}>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 32, fontWeight: 500, color: "var(--ink)", lineHeight: 1 }}>
              {result.risk_label}
            </span>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", borderTop: "1px solid var(--border)", marginTop: "20px" }}>
          {[
            { label: `Pontuação (${indexName})`, value: `${result.score} pt${result.score !== 1 ? "s" : ""}` },
            { label: "Cap. Funcional", value: `${result.mets} METs` },
            { label: "Cirurgia", value: result.surgery_label },
            { label: "Risco do Procedimento", value: result.surgery_risk === 'low' ? 'Baixo' : result.surgery_risk === 'high' ? 'Alto' : 'Intermediário' },
          ].map((cell, i) => (
            <div
              key={cell.label}
              style={{
                padding: "14px 16px",
                borderRight: i % 2 === 0 ? "1px solid var(--border)" : "none",
                borderBottom: i < 2 ? "1px solid var(--border)" : "none",
              }}
            >
              <div style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--ink-muted)", fontWeight: 600, marginBottom: 4 }}>
                {cell.label}
              </div>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 16, fontWeight: 500, color: "var(--ink)" }}>
                {cell.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {result.medication_advice.length > 0 && (
        <>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--ink-muted)", padding: "0 2px" }}>
            Manejo de Medicamentos
          </div>
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
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: "var(--ink)" }}>
                    💊 {med.medication}
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
        </>
      )}

      {result.recommended_exams.length > 0 && (
        <div
          style={{
            background: "var(--white)",
            borderRadius: "var(--r)",
            border: "1px solid var(--border)",
            padding: 16,
            boxShadow: "0 1px 4px rgba(13,17,23,0.06)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <div style={{ width: 28, height: 28, borderRadius: 8, background: "var(--blue-soft)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13 }}>
              🧪
            </div>
            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--ink)" }}>Exames Recomendados</span>
          </div>
          <div style={{ fontSize: 11, color: "var(--amber)", background: "var(--amber-soft)", padding: "6px 10px", borderRadius: 6, marginBottom: 10, fontWeight: 500 }}>
            ⚠️ Realizar antes do procedimento cirúrgico
          </div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "var(--ink-mid)", lineHeight: 1.8 }}>
            {result.recommended_exams.map((exam, i) => (
              <li key={i}>{exam}</li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--ink-muted)", padding: "0 2px" }}>
        Recomendações
      </div>

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
            <span style={{ fontSize: 18, flexShrink: 0 }}>{rec.icon}</span>
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

      <div
        style={{
          background: "var(--white)",
          borderRadius: "var(--r)",
          border: "1px solid var(--border)",
          padding: 16,
          boxShadow: "0 1px 4px rgba(13,17,23,0.06)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <div style={{ width: 28, height: 28, borderRadius: 8, background: "var(--blue-soft)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13 }}>
            📋
          </div>
          <span style={{ fontSize: 13, fontWeight: 600, color: "var(--ink)" }}>Fatores Identificados</span>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {result.risk_factors.map((f, i) => (
            <span
              key={i}
              style={{ fontSize: 11, padding: "4px 10px", borderRadius: 999, background: "var(--bg)", border: "1px solid var(--border)", color: "var(--ink-muted)", fontWeight: 500 }}
            >
              {f}
            </span>
          ))}
        </div>
      </div>

      <button
        onClick={() => generateReport(result, data)}
        style={{
          width: "100%",
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
        <span style={{ fontSize: 18 }}>📄</span>
        Baixar Relatório em PDF
      </button>

      <p style={{ textAlign: "center", fontSize: 10, color: "var(--ink-muted)", lineHeight: 1.7, padding: "0 8px" }}>
        Ferramenta de suporte clínico. Não substitui o julgamento médico individualizado.
        <br />
        Baseado na Diretriz Brasileira de Avaliação Cardiovascular Perioperatória, RCRI (Lee) e VSG.
      </p>
    </>
  );
}
