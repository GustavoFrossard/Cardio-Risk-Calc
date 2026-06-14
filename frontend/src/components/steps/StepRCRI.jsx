import { CalendarDays, HeartPulse } from "lucide-react";
import { Card, ToggleRow, InfoBox } from "../ui";

const CRITERIOS_RCRI = [
  {
    key: "rcri_cirurgia_alto_risco",
    rotulo: "Cirurgia de alto risco",
    descricao: "Intraperitoneal, intratorácica ou vascular suprainguinal",
  },
  {
    key: "rcri_doenca_coronaria",
    rotulo: "Doença arterial coronária",
    descricao: "Ondas Q, sintomas de isquemia, teste positivo, uso de nitrato",
  },
  {
    key: "rcri_ic",
    rotulo: "Insuficiência cardíaca congestiva",
    descricao: "Clínica de ICC ou RX de tórax com congestão",
  },
  {
    key: "rcri_cerebrovascular",
    rotulo: "Doença cerebrovascular",
    descricao: "AVC ou AIT prévios",
  },
  {
    key: "rcri_diabetes_insulina",
    rotulo: "Diabetes com insulinoterapia",
    descricao: "Em uso de insulina no pré-operatório",
  },
  {
    key: "rcri_creatinina_acima_2",
    rotulo: "Creatinina pré-operatória > 2,0 mg/dL",
    descricao: "Insuficiência renal pré-operatória",
  },
];

const VSG_FAIXA_ETARIA = [
  { valor: "lt60", rotulo: "< 60 anos", pontos: 0 },
  { valor: "60_69", rotulo: "60–69 anos", pontos: 2 },
  { valor: "70_79", rotulo: "70–79 anos", pontos: 3 },
  { valor: "gte80", rotulo: "≥ 80 anos", pontos: 4 },
];

const CRITERIOS_VSG = [
  { key: "vsg_dac", rotulo: "Doença arterial coronariana", descricao: "DAC documentada ou tratada", pontos: 2 },
  { key: "vsg_ic", rotulo: "Insuficiência cardíaca", descricao: "ICC prévia ou atual", pontos: 2 },
  { key: "vsg_dpoc", rotulo: "DPOC", descricao: "Doença pulmonar obstrutiva crônica", pontos: 2 },
  { key: "vsg_creatinina_acima_1_8", rotulo: "Creatinina > 1,8 mg/dL", descricao: "Insuficiência renal", pontos: 2 },
  { key: "vsg_tabagismo", rotulo: "Tabagismo", descricao: "Tabagista atual", pontos: 1 },
  { key: "vsg_diabetes_insulina", rotulo: "Diabetes com uso de insulina", descricao: "DM em insulinoterapia", pontos: 1 },
  { key: "vsg_betabloqueador_cronico", rotulo: "Uso crônico de betabloqueador", descricao: "Betabloqueador regular pré-operatório", pontos: 1 },
  { key: "vsg_revasc_previa", rotulo: "Revascularização miocárdica prévia", descricao: "Cirurgia ou angioplastia coronária", pontos: -1 },
];

export function EtapaRCRI({ data, onChange }) {
  const iconProps = { size: 16, strokeWidth: 2.2 };
  const ehVascular = data.eh_vascular;
  const nomeIndice = ehVascular ? "VSG" : "RCRI";

  let pontuacao;
  if (ehVascular) {
    const opcaoFaixa = VSG_FAIXA_ETARIA.find((o) => o.valor === data.vsg_faixa_etaria);
    pontuacao = (opcaoFaixa?.pontos ?? 0) + CRITERIOS_VSG.reduce((s, c) => s + (data[c.key] ? c.pontos : 0), 0);
    if (pontuacao < 0) pontuacao = 0;
  } else {
    pontuacao = CRITERIOS_RCRI.filter((c) => data[c.key] === true).length;
  }

  return (
    <>
      <InfoBox>
        {ehVascular ? (
          <>
            Cirurgia vascular identificada → usando <strong>Índice VSG-CRI</strong>. Os pontos variam conforme o critério.
          </>
        ) : (
          <>
            Cirurgia não vascular → usando <strong>Índice RCRI</strong>. Marque cada critério presente. Cada item soma <strong>+1 ponto</strong>.
          </>
        )}
      </InfoBox>

      {ehVascular ? (
        <>
          <Card icon={<CalendarDays {...iconProps} />} title="Faixa etária">
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {VSG_FAIXA_ETARIA.map((opt) => (
                <label
                  key={opt.valor}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "8px 4px",
                    cursor: "pointer",
                    borderRadius: 6,
                    background: data.vsg_faixa_etaria === opt.valor ? "var(--blue-soft)" : "transparent",
                  }}
                >
                  <input
                    type="radio"
                    name="vsg_faixa_etaria"
                    checked={data.vsg_faixa_etaria === opt.valor}
                    onChange={() => onChange("vsg_faixa_etaria", opt.valor)}
                    style={{ accentColor: "var(--blue)" }}
                  />
                  <span style={{ flex: 1, fontSize: 13, fontWeight: 500, color: "var(--ink)" }}>
                    {opt.rotulo}
                  </span>
                  <span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 11,
                      fontWeight: 500,
                      color: opt.pontos > 0 ? "var(--blue)" : "var(--ink-muted)",
                      background: opt.pontos > 0 ? "var(--blue-soft)" : "var(--bg-soft)",
                      padding: "2px 7px",
                      borderRadius: 4,
                    }}
                  >
                    {opt.pontos > 0 ? `+${opt.pontos}` : "0"}
                  </span>
                </label>
              ))}
            </div>
          </Card>

          <Card icon={<HeartPulse {...iconProps} />} title="Critérios do VSG-CRI">
            {CRITERIOS_VSG.map((criterio, i) => (
              <ToggleRow
                key={criterio.key}
                label={criterio.rotulo}
                description={criterio.descricao}
                checked={Boolean(data[criterio.key])}
                onChange={(val) => onChange(criterio.key, val)}
                badge={criterio.pontos > 0 ? `+${criterio.pontos}` : `${criterio.pontos}`}
                isLast={i === CRITERIOS_VSG.length - 1}
              />
            ))}
          </Card>
        </>
      ) : (
        <Card icon={<HeartPulse {...iconProps} />} title="Critérios do RCRI">
          {CRITERIOS_RCRI.map((criterio, i) => (
            <ToggleRow
              key={criterio.key}
              label={criterio.rotulo}
              description={criterio.descricao}
              checked={Boolean(data[criterio.key])}
              onChange={(val) => onChange(criterio.key, val)}
              badge="+1"
              isLast={i === CRITERIOS_RCRI.length - 1}
            />
          ))}
        </Card>
      )}

      {(() => {
        const isBaixo = ehVascular ? pontuacao <= 4 : pontuacao <= 1;
        const isInt = ehVascular ? pontuacao >= 5 && pontuacao <= 6 : pontuacao === 2;
        const bg = isBaixo ? "var(--green-soft)" : isInt ? "var(--amber-soft)" : "var(--red-soft)";
        const borderC = isBaixo ? "#A7D4BB" : isInt ? "#FCD34D" : "#F5B0AA";
        const color = isBaixo ? "var(--green)" : isInt ? "var(--amber)" : "var(--red)";
        return (
          <div style={{ background: bg, border: `1px solid ${borderC}`, borderRadius: "var(--r-sm)", padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 13, fontWeight: 500, color: "var(--ink-mid)" }}>Score {nomeIndice} atual</span>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 22, fontWeight: 600, color }}>
              {pontuacao} <span style={{ fontSize: 13 }}>pt{pontuacao !== 1 ? "s" : ""}</span>
            </span>
          </div>
        );
      })()}
    </>
  );
}
