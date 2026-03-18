import { Card, ToggleRow, InfoBox, Select } from "../ui";
import type { PatientData, SurgeryRisk } from "../../types";
import { SURGERY_OPTIONS } from "../../types";

interface Props {
  data: PatientData;
  onChange: <K extends keyof PatientData>(key: K, value: PatientData[K]) => void;
}

const RISK_GROUPS: Array<{ label: string; risk: SurgeryRisk }> = [
  { label: "Baixo Risco (< 1%)", risk: "low" },
  { label: "Risco Intermediário (1–5%)", risk: "intermediate" },
  { label: "Alto Risco (> 5%)", risk: "high" },
];

const CV_CONDITIONS: Array<{ key: keyof PatientData; label: string; description: string }> = [
  {
    key: "cv_acute_coronary",
    label: "Síndrome coronariana aguda",
    description: "IAM agudo (< 30 dias) ou angina instável",
  },
  {
    key: "cv_unstable_aortic",
    label: "Doenças instáveis da aorta torácica",
    description: "Dissecção aguda, aneurisma sintomático",
  },
  {
    key: "cv_acute_pulmonary_edema",
    label: "Edema agudo dos pulmões",
    description: "Episódio atual ou recente",
  },
  {
    key: "cv_cardiogenic_shock",
    label: "Choque cardiogênico",
    description: "Hipoperfusão por causa cardíaca",
  },
  {
    key: "cv_hf_nyha_3_4",
    label: "IC classe funcional III/IV (NYHA)",
    description: "Dispneia aos pequenos esforços ou em repouso",
  },
  {
    key: "cv_angina_ccs_3_4",
    label: "Angina classe funcional CCS III/IV",
    description: "Angina em atividades leves ou em repouso",
  },
  {
    key: "cv_severe_arrhythmia",
    label: "Bradiarritmias ou taquiarritmias graves",
    description: "BAVT, TV sustentada, arritmias sintomáticas",
  },
  {
    key: "cv_uncontrolled_hypertension",
    label: "HAS não controlada",
    description: "PA > 180 × 110 mmHg",
  },
  {
    key: "cv_af_high_rate",
    label: "FA de alta resposta ventricular",
    description: "FC > 120 bpm",
  },
  {
    key: "cv_pulmonary_hypertension",
    label: "HAP sintomática",
    description: "Hipertensão arterial pulmonar com sintomas",
  },
  {
    key: "cv_severe_valvular",
    label: "Estenose aórtica/mitral importante sintomática",
    description: "Estenose valvar grave com repercussão hemodinâmica",
  },
];

export function StepSurgery({ data, onChange }: Props) {
  const handleSurgeryChange = (value: string) => {
    const option = SURGERY_OPTIONS.find((o) => o.value === value);
    onChange("surgery_type", value);
    onChange("surgery_risk", option?.risk ?? "");
    onChange("is_vascular", option?.vascular ?? false);
  };

  const selectedOption = SURGERY_OPTIONS.find((o) => o.value === data.surgery_type);
  const riskBadge = selectedOption
    ? { low: "Baixo", intermediate: "Intermediário", high: "Alto" }[selectedOption.risk]
    : null;

  return (
    <>
      {/* Surgery Selection */}
      <Card icon="🏥" title="Identificação da Cirurgia (Tabela 3)">
        <Select value={data.surgery_type} onChange={(e) => handleSurgeryChange(e.target.value)}>
          <option value="">Selecione o procedimento...</option>
          {RISK_GROUPS.map((group) => (
            <optgroup key={group.risk} label={group.label}>
              {SURGERY_OPTIONS.filter((o) => o.risk === group.risk).map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </optgroup>
          ))}
        </Select>

        {selectedOption && (
          <div
            style={{
              marginTop: 12,
              display: "flex",
              gap: 8,
              flexWrap: "wrap",
            }}
          >
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                padding: "4px 10px",
                borderRadius: 999,
                background:
                  selectedOption.risk === "low"
                    ? "var(--green-soft)"
                    : selectedOption.risk === "intermediate"
                    ? "var(--amber-soft)"
                    : "var(--red-soft)",
                color:
                  selectedOption.risk === "low"
                    ? "var(--green)"
                    : selectedOption.risk === "intermediate"
                    ? "var(--amber)"
                    : "var(--red)",
              }}
            >
              Risco {riskBadge}
            </span>
            {selectedOption.vascular && (
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  padding: "4px 10px",
                  borderRadius: 999,
                  background: "var(--blue-soft)",
                  color: "var(--blue)",
                }}
              >
                Cirurgia Vascular → VSG
              </span>
            )}
          </div>
        )}
      </Card>

      {/* Active CV Conditions */}
      <Card icon="🚨" title="Condições Cardiovasculares Ativas (Tabela 2)">
        <InfoBox icon="⚠️">
          Condições que requerem avaliação e tratamento <strong>antes</strong> do procedimento cirúrgico.
        </InfoBox>
        <div style={{ marginTop: 10 }}>
          {CV_CONDITIONS.map((item, i) => (
            <ToggleRow
              key={item.key}
              label={item.label}
              description={item.description}
              checked={Boolean(data[item.key])}
              onChange={(val) => onChange(item.key, val as PatientData[typeof item.key])}
              isLast={i === CV_CONDITIONS.length - 1}
            />
          ))}
        </div>
      </Card>
    </>
  );
}
