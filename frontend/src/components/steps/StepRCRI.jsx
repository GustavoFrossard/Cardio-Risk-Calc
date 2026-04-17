import { Card, ToggleRow, InfoBox } from "../ui";

const RCRI_CRITERIA = [
  {
    key: "rcri_high_risk_surgery",
    label: "Cirurgia de alto risco",
    description: "Intraperitoneal, intratorácica ou vascular suprainguinal",
  },
  {
    key: "rcri_ischemic_heart",
    label: "Doença arterial coronária",
    description: "Ondas Q, sintomas de isquemia, teste positivo, uso de nitrato",
  },
  {
    key: "rcri_heart_failure",
    label: "Insuficiência cardíaca congestiva",
    description: "Clínica de ICC ou RX de tórax com congestão",
  },
  {
    key: "rcri_cerebrovascular",
    label: "Doença cerebrovascular",
    description: "AVC ou AIT prévios",
  },
  {
    key: "rcri_insulin_diabetes",
    label: "Diabetes com insulinoterapia",
    description: "Em uso de insulina no pré-operatório",
  },
  {
    key: "rcri_creatinine_above_2",
    label: "Creatinina pré-operatória > 2,0 mg/dL",
    description: "Insuficiência renal pré-operatória",
  },
];

const VSG_AGE_SELECT = [
  { value: "lt60", label: "< 60 anos", points: 0 },
  { value: "60_69", label: "60–69 anos", points: 2 },
  { value: "70_79", label: "70–79 anos", points: 3 },
  { value: "gte80", label: "≥ 80 anos", points: 4 },
];

const VSG_CRITERIA = [
  { key: "vsg_cad", label: "Doença arterial coronariana", description: "DAC documentada ou tratada", points: 2 },
  { key: "vsg_chf", label: "Insuficiência cardíaca", description: "ICC prévia ou atual", points: 2 },
  { key: "vsg_copd", label: "DPOC", description: "Doença pulmonar obstrutiva crônica", points: 2 },
  { key: "vsg_creatinine_over_1_8", label: "Creatinina > 1,8 mg/dL", description: "Insuficiência renal", points: 2 },
  { key: "vsg_smoking", label: "Tabagismo", description: "Tabagista atual", points: 1 },
  { key: "vsg_insulin_diabetes", label: "Diabetes com uso de insulina", description: "DM em insulinoterapia", points: 1 },
  { key: "vsg_chronic_beta_blocker", label: "Uso crônico de betabloqueador", description: "Betabloqueador regular pré-operatório", points: 1 },
  { key: "vsg_prior_revasc", label: "Revascularização miocárdica prévia", description: "Cirurgia ou angioplastia coronária", points: -1 },
];

export function StepRCRI({ data, onChange }) {
  const isVascular = data.is_vascular;
  const indexName = isVascular ? "VSG" : "RCRI";

  let score;
  if (isVascular) {
    const ageOpt = VSG_AGE_SELECT.find((o) => o.value === data.vsg_age_range);
    score = (ageOpt?.points ?? 0) + VSG_CRITERIA.reduce((s, c) => s + (data[c.key] ? c.points : 0), 0);
    if (score < 0) score = 0;
  } else {
    score = RCRI_CRITERIA.filter((c) => data[c.key] === true).length;
  }

  return (
    <>
      <InfoBox>
        {isVascular ? (
          <>
            Cirurgia vascular identificada → usando <strong>Índice VSG-CRI</strong> (Tabelas 6 e 7). Os pontos variam conforme o critério.
          </>
        ) : (
          <>
            Cirurgia não vascular → usando <strong>Índice RCRI</strong> (Tabelas 4 e 5). Marque cada critério presente. Cada item soma <strong>+1 ponto</strong>.
          </>
        )}
      </InfoBox>

      {isVascular ? (
        <>
          <Card icon="📅" title="Faixa etária">
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {VSG_AGE_SELECT.map((opt) => (
                <label
                  key={opt.value}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "8px 4px",
                    cursor: "pointer",
                    borderRadius: 6,
                    background: data.vsg_age_range === opt.value ? "var(--blue-soft)" : "transparent",
                  }}
                >
                  <input
                    type="radio"
                    name="vsg_age_range"
                    checked={data.vsg_age_range === opt.value}
                    onChange={() => onChange("vsg_age_range", opt.value)}
                    style={{ accentColor: "var(--blue)" }}
                  />
                  <span style={{ flex: 1, fontSize: 13, fontWeight: 500, color: "var(--ink)" }}>
                    {opt.label}
                  </span>
                  <span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 11,
                      fontWeight: 500,
                      color: opt.points > 0 ? "var(--blue)" : "var(--ink-muted)",
                      background: opt.points > 0 ? "var(--blue-soft)" : "var(--bg-soft)",
                      padding: "2px 7px",
                      borderRadius: 4,
                    }}
                  >
                    {opt.points > 0 ? `+${opt.points}` : "0"}
                  </span>
                </label>
              ))}
            </div>
          </Card>

          <Card icon="🫀" title="Critérios do VSG-CRI">
            {VSG_CRITERIA.map((criterion, i) => (
              <ToggleRow
                key={criterion.key}
                label={criterion.label}
                description={criterion.description}
                checked={Boolean(data[criterion.key])}
                onChange={(val) => onChange(criterion.key, val)}
                badge={criterion.points > 0 ? `+${criterion.points}` : `${criterion.points}`}
                isLast={i === VSG_CRITERIA.length - 1}
              />
            ))}
          </Card>
        </>
      ) : (
        <Card icon="🫀" title="Critérios do RCRI">
          {RCRI_CRITERIA.map((criterion, i) => (
            <ToggleRow
              key={criterion.key}
              label={criterion.label}
              description={criterion.description}
              checked={Boolean(data[criterion.key])}
              onChange={(val) => onChange(criterion.key, val)}
              badge="+1"
              isLast={i === RCRI_CRITERIA.length - 1}
            />
          ))}
        </Card>
      )}

      <div
        style={{
          background: score === 0 ? "var(--green-soft)" : score <= 2 ? "var(--amber-soft)" : "var(--red-soft)",
          border: `1px solid ${score === 0 ? "#A7D4BB" : score <= 2 ? "#FCD34D" : "#F5B0AA"}`,
          borderRadius: "var(--r-sm)",
          padding: "12px 16px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span style={{ fontSize: 13, fontWeight: 500, color: "var(--ink-mid)" }}>
          Score {indexName} atual
        </span>
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 22,
            fontWeight: 600,
            color: score === 0 ? "var(--green)" : score <= 2 ? "var(--amber)" : "var(--red)",
          }}
        >
          {score} <span style={{ fontSize: 13 }}>pt{score !== 1 ? "s" : ""}</span>
        </span>
      </div>
    </>
  );
}
