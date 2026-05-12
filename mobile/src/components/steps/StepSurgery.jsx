import { View, Text } from "react-native";
import { Card, ToggleRow, InfoBox, Select } from "../ui";
import { SURGERY_OPTIONS } from "../../types";
import { theme } from "../../theme";

const RISK_GROUPS = [
  { label: "Baixo Risco (< 1%)", risk: "low" },
  { label: "Risco Intermediário (1–5%)", risk: "intermediate" },
  { label: "Alto Risco (> 5%)", risk: "high" },
];

// Flat options list with section headers for the modal picker
const SURGERY_FLAT_OPTIONS = RISK_GROUPS.flatMap((group) => [
  { value: `__header_${group.risk}`, label: group.label, isHeader: true },
  ...SURGERY_OPTIONS.filter((o) => o.risk === group.risk).map((o) => ({
    value: o.value,
    label: o.label,
  })),
]);

const CV_CONDITIONS = [
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

export function EtapaCirurgia({ data, onChange }) {
  const handleSurgeryChange = (value) => {
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
      <Card icon="🏥" title="Identificação da Cirurgia">
        <Select
          value={data.surgery_type}
          onChange={handleSurgeryChange}
          options={SURGERY_FLAT_OPTIONS}
          placeholder="Selecione o procedimento..."
        />

        {selectedOption ? (
          <View style={{ marginTop: 12, flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
            <Text
              style={{
                fontSize: 11,
                fontWeight: "600",
                paddingVertical: 4,
                paddingHorizontal: 10,
                borderRadius: 999,
                backgroundColor:
                  selectedOption.risk === "low"
                    ? theme.greenSoft
                    : selectedOption.risk === "intermediate"
                    ? theme.amberSoft
                    : theme.redSoft,
                color:
                  selectedOption.risk === "low"
                    ? theme.green
                    : selectedOption.risk === "intermediate"
                    ? theme.amber
                    : theme.red,
              }}
            >
              Risco {riskBadge}
            </Text>
            {selectedOption.vascular ? (
              <Text
                style={{
                  fontSize: 11,
                  fontWeight: "600",
                  paddingVertical: 4,
                  paddingHorizontal: 10,
                  borderRadius: 999,
                  backgroundColor: theme.blueSoft,
                  color: theme.blue,
                }}
              >
                Cirurgia Vascular → VSG
              </Text>
            ) : null}
          </View>
        ) : null}
      </Card>

      <Card icon="🚨" title="Condições Cardiovasculares Ativas">
        <InfoBox icon="⚠️">
          <Text style={{ fontSize: 12, color: "#1A3B7A", lineHeight: 18.6 }}>
            Condições que requerem avaliação e tratamento{" "}
            <Text style={{ fontWeight: "bold" }}>antes</Text> do procedimento cirúrgico.
          </Text>
        </InfoBox>
        <View style={{ marginTop: 10 }}>
          {CV_CONDITIONS.map((item, i) => (
            <ToggleRow
              key={item.key}
              label={item.label}
              description={item.description}
              checked={Boolean(data[item.key])}
              onChange={(val) => onChange(item.key, val)}
              isLast={i === CV_CONDITIONS.length - 1}
            />
          ))}
        </View>
      </Card>
    </>
  );
}
