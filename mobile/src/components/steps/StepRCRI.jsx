import { View, Text, TouchableOpacity } from "react-native";
import { Card, ToggleRow, InfoBox } from "../ui";
import { theme } from "../../theme";

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

export function EtapaRCRI({ data, onChange }) {
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

  const scoreColor = score === 0 ? theme.green : score <= 2 ? theme.amber : theme.red;
  const scoreBg = score === 0 ? theme.greenSoft : score <= 2 ? theme.amberSoft : theme.redSoft;
  const scoreBorder = score === 0 ? "#A7D4BB" : score <= 2 ? "#FCD34D" : "#F5B0AA";

  return (
    <>
      <InfoBox>
        {isVascular ? (
          <Text style={{ fontSize: 12, color: "#1A3B7A", lineHeight: 18.6 }}>
            Cirurgia vascular identificada → usando{" "}
            <Text style={{ fontWeight: "bold" }}>Índice VSG-CRI</Text>. Os pontos
            variam conforme o critério.
          </Text>
        ) : (
          <Text style={{ fontSize: 12, color: "#1A3B7A", lineHeight: 18.6 }}>
            Cirurgia não vascular → usando{" "}
            <Text style={{ fontWeight: "bold" }}>Índice RCRI</Text>. Marque cada
            critério presente. Cada item soma{" "}
            <Text style={{ fontWeight: "bold" }}>+1 ponto</Text>.
          </Text>
        )}
      </InfoBox>

      {isVascular ? (
        <>
          <Card icon="📅" title="Faixa etária">
            <View style={{ gap: 6 }}>
              {VSG_AGE_SELECT.map((opt) => (
                <TouchableOpacity
                  key={opt.value}
                  onPress={() => onChange("vsg_age_range", opt.value)}
                  activeOpacity={0.7}
                  style={{
                    flexDirection: "row",
                    alignItems: "center",
                    gap: 10,
                    paddingVertical: 8,
                    paddingHorizontal: 4,
                    borderRadius: 6,
                    backgroundColor:
                      data.vsg_age_range === opt.value ? theme.blueSoft : "transparent",
                  }}
                >
                  {/* Custom radio button */}
                  <View
                    style={{
                      width: 18,
                      height: 18,
                      borderRadius: 9,
                      borderWidth: 2,
                      borderColor:
                        data.vsg_age_range === opt.value ? theme.blue : theme.border,
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    {data.vsg_age_range === opt.value ? (
                      <View
                        style={{
                          width: 9,
                          height: 9,
                          borderRadius: 5,
                          backgroundColor: theme.blue,
                        }}
                      />
                    ) : null}
                  </View>

                  <Text
                    style={{
                      flex: 1,
                      fontSize: 13,
                      fontWeight: "500",
                      color: theme.ink,
                    }}
                  >
                    {opt.label}
                  </Text>

                  <Text
                    style={{
                      fontFamily: "monospace",
                      fontSize: 11,
                      fontWeight: "500",
                      color: opt.points > 0 ? theme.blue : theme.inkMuted,
                      backgroundColor: opt.points > 0 ? theme.blueSoft : theme.bgSoft,
                      paddingHorizontal: 7,
                      paddingVertical: 2,
                      borderRadius: 4,
                    }}
                  >
                    {opt.points > 0 ? `+${opt.points}` : "0"}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
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

      <View
        style={{
          backgroundColor: scoreBg,
          borderWidth: 1,
          borderColor: scoreBorder,
          borderRadius: theme.rSm,
          paddingVertical: 12,
          paddingHorizontal: 16,
          flexDirection: "row",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Text style={{ fontSize: 13, fontWeight: "500", color: theme.inkMid }}>
          Score {indexName} atual
        </Text>
        <Text
          style={{
            fontFamily: "monospace",
            fontSize: 22,
            fontWeight: "600",
            color: scoreColor,
          }}
        >
          {score}{" "}
          <Text style={{ fontSize: 13 }}>pt{score !== 1 ? "s" : ""}</Text>
        </Text>
      </View>
    </>
  );
}
