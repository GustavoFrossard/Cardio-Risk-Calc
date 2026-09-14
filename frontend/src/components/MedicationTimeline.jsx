import { Fragment } from "react";

const TOM = {
  verde: { texto: "var(--green)", fundo: "var(--green-soft)", borda: "var(--green-border)" },
  amarelo: { texto: "var(--amber)", fundo: "var(--amber-soft)", borda: "var(--amber-border)" },
  vermelho: { texto: "var(--red)", fundo: "var(--red-soft)", borda: "var(--red-border)" },
};

function tomDe(tipo) {
  return TOM[tipo] ?? TOM.amarelo;
}

const LABEL_W = 96;
const LABEL_GAP = 10;
const ROW_H = 22;

export function LinhaTempoMedicacoes({ orientacoes }) {
  const suspensoes = orientacoes.filter((m) => m.dias_antes != null);
  const mantidos = orientacoes.filter((m) => m.dias_antes == null);

  if (suspensoes.length === 0) {
    return null;
  }

  const maxPre = Math.max(...suspensoes.map((m) => m.dias_antes));
  const maxPost = Math.max(1, ...suspensoes.map((m) => m.retorno_dias_depois ?? 1));
  const totalDias = maxPre + maxPost;

  const pctPre = (dia) => ((maxPre - dia) / totalDias) * 100;
  const pctPos = (dia) => ((maxPre + dia) / totalDias) * 100;
  const pctCirurgia = (maxPre / totalDias) * 100;

  const ticksPre = [...new Set(suspensoes.map((m) => m.dias_antes))].sort((a, b) => b - a);
  const ticksPos = [...new Set(suspensoes.map((m) => m.retorno_dias_depois).filter((d) => d != null))].sort((a, b) => a - b);

  return (
    <div
      style={{
        background: "var(--white)",
        borderRadius: "var(--r)",
        border: "1px solid var(--border)",
        padding: "18px 16px 16px",
        boxShadow: "0 1px 4px rgba(13,17,23,0.06)",
      }}
    >
      <div style={{ fontSize: 11, color: "var(--ink-muted)", marginBottom: 14, fontWeight: 500 }}>
        Dias em relação à cirurgia — faixa colorida indica o período suspenso
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: `${LABEL_W}px 1fr`,
          columnGap: LABEL_GAP,
          rowGap: 10,
          alignItems: "center",
        }}
      >
        {suspensoes.map((m) => {
          const tom = tomDe(m.tipo);
          const startPct = pctPre(m.dias_antes);
          const endPct = m.retorno_dias_depois != null ? pctPos(m.retorno_dias_depois) : pctCirurgia;
          return (
            <Fragment key={m.medicamento}>
              <div
                title={m.medicamento}
                style={{
                  fontSize: 11, fontWeight: 600, color: "var(--ink)",
                  whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                }}
              >
                {m.medicamento}
              </div>
              <div style={{ position: "relative", height: ROW_H }}>
                <div style={{ position: "absolute", left: 0, right: 0, top: "50%", height: 1, background: "var(--border)", transform: "translateY(-50%)" }} />
                <div
                  title={`${m.acao}${m.retorno_dias_depois != null ? ` · retorno D+${m.retorno_dias_depois}` : ""}`}
                  style={{
                    position: "absolute", top: 0, bottom: 0,
                    left: `${startPct}%`, width: `${Math.max(endPct - startPct, 3)}%`,
                    background: tom.fundo, border: `1px solid ${tom.borda}`, borderRadius: 5,
                  }}
                />
              </div>
            </Fragment>
          );
        })}

        {/* eixo */}
        <div />
        <div style={{ position: "relative", height: 16, marginTop: 6 }}>
          {ticksPre.map((dia) => (
            <span
              key={`pre-${dia}`}
              style={{ position: "absolute", left: `${pctPre(dia)}%`, transform: "translateX(-50%)", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--ink-muted)", whiteSpace: "nowrap" }}
            >
              D-{dia}
            </span>
          ))}
          <span
            style={{ position: "absolute", left: `${pctCirurgia}%`, transform: "translateX(-50%)", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 700, color: "var(--ink)", whiteSpace: "nowrap" }}
          >
            Cirurgia
          </span>
          {ticksPos.map((dia) => (
            <span
              key={`pos-${dia}`}
              style={{ position: "absolute", left: `${pctPos(dia)}%`, transform: "translateX(-50%)", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--ink-muted)", whiteSpace: "nowrap" }}
            >
              D+{dia}
            </span>
          ))}
        </div>
      </div>

      {mantidos.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 16, paddingTop: 12, borderTop: "1px solid var(--bg-soft)" }}>
          {mantidos.map((m) => {
            const tom = tomDe(m.tipo);
            return (
              <div key={m.medicamento} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: tom.texto, flexShrink: 0 }} />
                <div style={{ flex: 1, fontSize: 12.5, color: "var(--ink)" }}>{m.medicamento}</div>
                <div style={{ fontSize: 11, fontWeight: 600, color: tom.texto, background: tom.fundo, borderRadius: 999, padding: "3px 10px" }}>
                  {m.acao}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
