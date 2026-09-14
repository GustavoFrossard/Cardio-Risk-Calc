const TOM = {
  verde: { texto: "var(--green)", fundo: "var(--green-soft)", borda: "var(--green-border)" },
  amarelo: { texto: "var(--amber)", fundo: "var(--amber-soft)", borda: "var(--amber-border)" },
  vermelho: { texto: "var(--red)", fundo: "var(--red-soft)", borda: "var(--red-border)" },
};

function tomDe(tipo) {
  return TOM[tipo] ?? TOM.amarelo;
}

const LINHA_BOTTOM = 24;
const HASTE_BASE = 10;
const HASTE_PASSO = 34;
const BOLHA_ALTURA = 30;
const GAP_MINIMO_PCT = 20;
// Duas bolhas da mesma cor exigem mais distância entre si — do contrário
// ficam parecendo o mesmo item mesmo quando os dias são diferentes.
const GAP_MINIMO_MESMA_COR_PCT = 32;

// Agrupa por dia e, quando dois grupos vizinhos ficam próximos demais no eixo
// (bolhas colidiriam ou se confundiriam por terem a mesma cor), escalona o
// grupo mais à direita para uma haste mais alta.
function dispor(diasUnicos, porDia, pctFn) {
  let pctAnterior = null;
  let lanesAnterior = 0;
  let tipoAnterior = null;
  return diasUnicos.map((dia) => {
    const pct = pctFn(dia);
    const itens = porDia[dia];
    const tipoAtual = itens[0].tipo;
    const gapNecessario = tipoAtual === tipoAnterior ? GAP_MINIMO_MESMA_COR_PCT : GAP_MINIMO_PCT;
    const laneBase = pctAnterior != null && pct - pctAnterior < gapNecessario ? lanesAnterior : 0;
    pctAnterior = pct;
    lanesAnterior = laneBase + itens.length;
    tipoAnterior = tipoAtual;
    return { dia, pct, itens, laneBase };
  });
}

export function LinhaTempoMedicacoes({ orientacoes }) {
  const suspensoes = orientacoes.filter((m) => m.dias_antes != null);
  const mantidos = orientacoes.filter((m) => m.dias_antes == null);

  if (suspensoes.length === 0) {
    return null;
  }

  const maxPre = Math.max(...suspensoes.map((m) => m.dias_antes));
  const maxPos = Math.max(1, ...suspensoes.map((m) => m.retorno_dias_depois ?? 1));
  const totalDias = maxPre + maxPos;
  const pctPre = (dia) => ((maxPre - dia) / totalDias) * 100;
  const pctPos = (dia) => ((maxPre + dia) / totalDias) * 100;
  const pctCirurgia = (maxPre / totalDias) * 100;

  const diasUnicosPre = [...new Set(suspensoes.map((m) => m.dias_antes))].sort((a, b) => b - a);
  const porDiaPre = {};
  suspensoes.forEach((m) => {
    (porDiaPre[m.dias_antes] ??= []).push(m);
  });

  const diasUnicosPos = [...new Set(suspensoes.map((m) => m.retorno_dias_depois ?? 1))].sort((a, b) => a - b);
  const porDiaPos = {};
  suspensoes.forEach((m) => {
    const dia = m.retorno_dias_depois ?? 1;
    (porDiaPos[dia] ??= []).push(m);
  });

  const gruposPre = dispor(diasUnicosPre, porDiaPre, pctPre);
  const gruposPos = dispor(diasUnicosPos, porDiaPos, pctPos);

  const maxLanes = Math.max(
    1,
    ...gruposPre.map((g) => g.laneBase + g.itens.length),
    ...gruposPos.map((g) => g.laneBase + g.itens.length),
  );
  const alturaTimeline = LINHA_BOTTOM + HASTE_BASE + (maxLanes - 1) * HASTE_PASSO + BOLHA_ALTURA + 8;

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
      <div style={{ fontSize: 11, color: "var(--ink-muted)", marginBottom: 4, fontWeight: 500 }}>
        Dias em relação à cirurgia — {"↩"} indica retorno da medicação
      </div>

      <div style={{ position: "relative", width: "100%", height: alturaTimeline, margin: "8px 0 8px" }}>
        {/* linha base */}
        <div style={{ position: "absolute", left: 0, right: 0, bottom: LINHA_BOTTOM, height: 1.5, background: "var(--border)" }} />

        {/* marcador da cirurgia */}
        <div
          style={{
            position: "absolute", left: `${pctCirurgia}%`, bottom: LINHA_BOTTOM - 4, width: 9, height: 9, borderRadius: "50%",
            background: "var(--ink)", border: "2px solid var(--white)", transform: "translateX(-50%)",
          }}
        />
        <div
          style={{
            position: "absolute", left: `${pctCirurgia}%`, bottom: 0, transform: "translateX(-50%)",
            fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, fontWeight: 600, color: "var(--ink)", whiteSpace: "nowrap",
          }}
        >
          Cirurgia
        </div>

        {gruposPre.map(({ dia, pct, itens: grupo, laneBase }) => {
          return (
            <div key={`pre-${dia}`}>
              <div
                style={{
                  position: "absolute", left: `${pct}%`, bottom: 0, transform: "translateX(-50%)",
                  fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: "var(--ink-muted)", whiteSpace: "nowrap",
                }}
              >
                D-{dia}
              </div>
              <div
                style={{
                  position: "absolute", left: `${pct}%`, bottom: LINHA_BOTTOM - 4, width: 8, height: 8, borderRadius: "50%",
                  transform: "translateX(-50%)", background: tomDe(grupo[0].tipo).texto, border: "2px solid var(--white)",
                  boxShadow: `0 0 0 1px ${tomDe(grupo[0].tipo).borda}`,
                }}
              />
              {grupo.map((m, i) => {
                const tom = tomDe(m.tipo);
                const hasteAltura = HASTE_BASE + (laneBase + i) * HASTE_PASSO;
                return (
                  <div key={m.medicamento}>
                    <div
                      style={{
                        position: "absolute", left: `${pct}%`, bottom: LINHA_BOTTOM, width: 1.5, height: hasteAltura,
                        background: tom.borda, transform: "translateX(-50%)",
                      }}
                    />
                    <div
                      style={{
                        position: "absolute",
                        left: `${pct}%`,
                        bottom: LINHA_BOTTOM + hasteAltura,
                        transform: "translateX(-50%)",
                        background: tom.fundo,
                        border: `1px solid ${tom.borda}`,
                        borderRadius: 8,
                        padding: "4px 9px",
                        fontSize: 10.5,
                        fontWeight: 600,
                        color: tom.texto,
                        whiteSpace: "nowrap",
                      }}
                    >
                      {m.medicamento}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })}

        {gruposPos.map(({ dia, pct, itens: grupo, laneBase }) => {
          return (
            <div key={`pos-${dia}`}>
              <div
                style={{
                  position: "absolute", left: `${pct}%`, bottom: 0, transform: "translateX(-50%)",
                  fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: "var(--ink-muted)", whiteSpace: "nowrap",
                }}
              >
                D+{dia}
              </div>
              <div
                style={{
                  position: "absolute", left: `${pct}%`, bottom: LINHA_BOTTOM - 3, width: 6, height: 6, borderRadius: "50%",
                  transform: "translateX(-50%)", background: "var(--white)", border: `2px solid ${tomDe(grupo[0].tipo).texto}`,
                }}
              />
              {grupo.map((m, i) => {
                const tom = tomDe(m.tipo);
                const hasteAltura = HASTE_BASE + (laneBase + i) * HASTE_PASSO;
                return (
                  <div key={`pos-${m.medicamento}`}>
                    <div
                      style={{
                        position: "absolute", left: `${pct}%`, bottom: LINHA_BOTTOM, width: 0, height: hasteAltura,
                        borderLeft: `1.5px dashed ${tom.borda}`, transform: "translateX(-50%)",
                      }}
                    />
                    <div
                      style={{
                        position: "absolute",
                        left: `${pct}%`,
                        bottom: LINHA_BOTTOM + hasteAltura,
                        transform: "translateX(-50%)",
                        background: "var(--white)",
                        border: `1px dashed ${tom.borda}`,
                        borderRadius: 8,
                        padding: "4px 9px",
                        fontSize: 10.5,
                        fontWeight: 500,
                        color: tom.texto,
                        whiteSpace: "nowrap",
                      }}
                    >
                      {"↩"} {m.medicamento}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>

      {mantidos.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 4, paddingTop: 12, borderTop: "1px solid var(--bg-soft)" }}>
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
