import { View, Text, TouchableOpacity } from "react-native";
import { generateReport } from "../../services/report";
import { theme } from "../../theme";

const REC_COLORS = {
  green: { border: theme.green, bg: theme.greenSoft },
  amber: { border: theme.amber, bg: theme.amberSoft },
  red: { border: theme.red, bg: theme.redSoft },
};

const PILL_COLORS = {
  low: { bg: theme.greenSoft, color: theme.green },
  intermediate: { bg: theme.amberSoft, color: theme.amber },
  high: { bg: theme.redSoft, color: theme.red },
};

export function EtapaResultado({ result, data }) {
  const pill = PILL_COLORS[result.risk_class] ?? PILL_COLORS.low;
  const indexName = result.risk_index === "vsg" ? "VSG" : "RCRI";

  return (
    <>
      {result.has_active_conditions ? (
        <View
          style={{
            backgroundColor: theme.redSoft,
            borderWidth: 1,
            borderColor: "#F5B0AA",
            borderRadius: theme.r,
            padding: 14,
            flexDirection: "row",
            gap: 12,
            alignItems: "flex-start",
          }}
        >
          <Text style={{ fontSize: 20, flexShrink: 0 }}>🚨</Text>
          <View>
            <Text
              style={{
                fontSize: 13,
                fontWeight: "700",
                color: theme.red,
                marginBottom: 4,
              }}
            >
              Condições Cardíacas Ativas Detectadas
            </Text>
            {result.active_conditions.map((c, i) => (
              <Text
                key={i}
                style={{ fontSize: 12, color: theme.inkMid, lineHeight: 19, marginLeft: 2 }}
              >
                • {c}
              </Text>
            ))}
            <Text
              style={{ fontSize: 11, color: theme.red, marginTop: 6, fontWeight: "500" }}
            >
              Avaliar e tratar antes do procedimento cirúrgico.
            </Text>
          </View>
        </View>
      ) : null}

      {/* Risk summary card */}
      <View
        style={{
          backgroundColor: theme.white,
          borderRadius: theme.r,
          borderWidth: 1,
          borderColor: theme.border,
          overflow: "hidden",
          shadowColor: "#0D1117",
          shadowOffset: { width: 0, height: 1 },
          shadowOpacity: 0.06,
          shadowRadius: 4,
          elevation: 2,
        }}
      >
        <View style={{ padding: 20, paddingBottom: 0 }}>
          <Text
            style={{
              fontSize: 10,
              textTransform: "uppercase",
              letterSpacing: 1,
              fontWeight: "600",
              color: theme.inkMuted,
              marginBottom: 6,
            }}
          >
            Estratificação de Risco ({indexName})
          </Text>
          <Text
            style={{
              fontFamily: "monospace",
              fontSize: 32,
              fontWeight: "500",
              color: theme.ink,
              lineHeight: 38,
              marginBottom: 8,
            }}
          >
            {result.risk_label}
          </Text>
        </View>

        {/* 2-column grid */}
        <View
          style={{
            flexDirection: "row",
            flexWrap: "wrap",
            borderTopWidth: 1,
            borderTopColor: theme.border,
            marginTop: 20,
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
            <View
              key={cell.label}
              style={{
                width: "50%",
                padding: 14,
                borderRightWidth: i % 2 === 0 ? 1 : 0,
                borderRightColor: theme.border,
                borderBottomWidth: i < 2 ? 1 : 0,
                borderBottomColor: theme.border,
              }}
            >
              <Text
                style={{
                  fontSize: 10,
                  textTransform: "uppercase",
                  letterSpacing: 0.8,
                  color: theme.inkMuted,
                  fontWeight: "600",
                  marginBottom: 4,
                }}
              >
                {cell.label}
              </Text>
              <Text
                style={{
                  fontFamily: "monospace",
                  fontSize: 14,
                  fontWeight: "500",
                  color: theme.ink,
                }}
                numberOfLines={2}
              >
                {cell.value}
              </Text>
            </View>
          ))}
        </View>
      </View>

      {/* Medication advice */}
      {result.medication_advice.length > 0 ? (
        <>
          <Text
            style={{
              fontSize: 10,
              fontWeight: "700",
              textTransform: "uppercase",
              letterSpacing: 1,
              color: theme.inkMuted,
              paddingHorizontal: 2,
            }}
          >
            Manejo de Medicamentos
          </Text>
          {result.medication_advice.map((med, i) => {
            const colors = REC_COLORS[med.type] || REC_COLORS.amber;
            return (
              <View
                key={i}
                style={{
                  backgroundColor: theme.white,
                  borderRadius: theme.r,
                  borderWidth: 1,
                  borderColor: theme.border,
                  borderLeftWidth: 3,
                  borderLeftColor: colors.border,
                  padding: 14,
                  shadowColor: "#0D1117",
                  shadowOffset: { width: 0, height: 1 },
                  shadowOpacity: 0.06,
                  shadowRadius: 4,
                  elevation: 2,
                }}
              >
                <View
                  style={{
                    flexDirection: "row",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 4,
                  }}
                >
                  <Text style={{ fontSize: 13, fontWeight: "700", color: theme.ink }}>
                    💊 {med.medication}
                  </Text>
                  <Text
                    style={{
                      fontSize: 11,
                      fontWeight: "600",
                      paddingVertical: 3,
                      paddingHorizontal: 8,
                      borderRadius: 999,
                      backgroundColor: colors.bg,
                      color: colors.border,
                    }}
                  >
                    {med.action}
                  </Text>
                </View>
                <Text style={{ fontSize: 12, color: theme.inkMid, lineHeight: 18.6 }}>
                  {med.detail}
                </Text>
              </View>
            );
          })}
        </>
      ) : null}

      {/* Recommended exams */}
      {result.recommended_exams.length > 0 ? (
        <View
          style={{
            backgroundColor: theme.white,
            borderRadius: theme.r,
            borderWidth: 1,
            borderColor: theme.border,
            padding: 16,
            shadowColor: "#0D1117",
            shadowOffset: { width: 0, height: 1 },
            shadowOpacity: 0.06,
            shadowRadius: 4,
            elevation: 2,
          }}
        >
          <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <View
              style={{
                width: 28,
                height: 28,
                borderRadius: 8,
                backgroundColor: theme.blueSoft,
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Text style={{ fontSize: 13 }}>🧪</Text>
            </View>
            <Text style={{ fontSize: 13, fontWeight: "600", color: theme.ink }}>
              Exames Recomendados
            </Text>
          </View>
          <Text
            style={{
              fontSize: 11,
              color: theme.amber,
              backgroundColor: theme.amberSoft,
              padding: 8,
              borderRadius: 6,
              marginBottom: 10,
              fontWeight: "500",
            }}
          >
            ⚠️ Realizar antes do procedimento cirúrgico
          </Text>
          {result.recommended_exams.map((exam, i) => (
            <Text
              key={i}
              style={{ fontSize: 12, color: theme.inkMid, lineHeight: 22, marginLeft: 2 }}
            >
              • {exam}
            </Text>
          ))}
        </View>
      ) : null}

      {/* Recommendations */}
      <Text
        style={{
          fontSize: 10,
          fontWeight: "700",
          textTransform: "uppercase",
          letterSpacing: 1,
          color: theme.inkMuted,
          paddingHorizontal: 2,
        }}
      >
        Recomendações
      </Text>

      {result.recommendations.map((rec, i) => {
        const colors = REC_COLORS[rec.type] || REC_COLORS.green;
        return (
          <View
            key={i}
            style={{
              backgroundColor: theme.white,
              borderRadius: theme.r,
              borderWidth: 1,
              borderColor: theme.border,
              borderLeftWidth: 3,
              borderLeftColor: colors.border,
              padding: 14,
              flexDirection: "row",
              gap: 12,
              alignItems: "flex-start",
              shadowColor: "#0D1117",
              shadowOffset: { width: 0, height: 1 },
              shadowOpacity: 0.06,
              shadowRadius: 4,
              elevation: 2,
            }}
          >
            <Text style={{ fontSize: 18, flexShrink: 0 }}>{rec.icon}</Text>
            <View>
              <Text
                style={{ fontSize: 13, fontWeight: "600", marginBottom: 3, color: theme.ink }}
              >
                {rec.title}
              </Text>
              <Text style={{ fontSize: 12, color: theme.inkMid, lineHeight: 18.6 }}>
                {rec.body}
              </Text>
            </View>
          </View>
        );
      })}

      {/* Risk factors */}
      <View
        style={{
          backgroundColor: theme.white,
          borderRadius: theme.r,
          borderWidth: 1,
          borderColor: theme.border,
          padding: 16,
          shadowColor: "#0D1117",
          shadowOffset: { width: 0, height: 1 },
          shadowOpacity: 0.06,
          shadowRadius: 4,
          elevation: 2,
        }}
      >
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <View
            style={{
              width: 28,
              height: 28,
              borderRadius: 8,
              backgroundColor: theme.blueSoft,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Text style={{ fontSize: 13 }}>📋</Text>
          </View>
          <Text style={{ fontSize: 13, fontWeight: "600", color: theme.ink }}>
            Fatores Identificados
          </Text>
        </View>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }}>
          {result.risk_factors.map((f, i) => (
            <Text
              key={i}
              style={{
                fontSize: 11,
                paddingVertical: 4,
                paddingHorizontal: 10,
                borderRadius: 999,
                backgroundColor: theme.bg,
                borderWidth: 1,
                borderColor: theme.border,
                color: theme.inkMuted,
                fontWeight: "500",
              }}
            >
              {f}
            </Text>
          ))}
        </View>
      </View>

      {/* PDF button */}
      <TouchableOpacity
        onPress={() => generateReport(result, data)}
        activeOpacity={0.85}
        style={{
          width: "100%",
          paddingVertical: 14,
          paddingHorizontal: 20,
          backgroundColor: theme.blue,
          borderRadius: theme.r,
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          shadowColor: "#0f4c81",
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.25,
          shadowRadius: 8,
          elevation: 4,
        }}
      >
        <Text style={{ fontSize: 18 }}>📄</Text>
        <Text style={{ fontSize: 14, fontWeight: "600", color: "white" }}>
          Baixar Relatório em PDF
        </Text>
      </TouchableOpacity>

      <Text
        style={{
          textAlign: "center",
          fontSize: 10,
          color: theme.inkMuted,
          lineHeight: 17,
          paddingHorizontal: 8,
          marginBottom: 8,
        }}
      >
        Ferramenta de suporte clínico. Não substitui o julgamento médico individualizado.{"\n"}
        Baseado na Diretriz Brasileira de Avaliação Cardiovascular Perioperatória, RCRI (Lee) e VSG.
      </Text>
    </>
  );
}
