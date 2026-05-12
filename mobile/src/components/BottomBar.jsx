import { View, Text, TouchableOpacity } from "react-native";
import { theme } from "../theme";

export function BarraInferior({ currentStep, totalSteps, isLoading, onBack, onNext, onReset }) {
  const isResult = currentStep === totalSteps;
  const isLastInput = currentStep === totalSteps - 1;

  const nextLabel = isLoading
    ? "Calculando..."
    : isResult
    ? "Nova Avaliação"
    : isLastInput
    ? "Calcular Risco"
    : "Próximo →";

  return (
    <View
      style={{
        backgroundColor: "rgba(255,255,255,0.97)",
        paddingHorizontal: 16,
        paddingTop: 12,
        paddingBottom: 24,
        borderTopWidth: 1,
        borderTopColor: theme.border,
        flexDirection: "row",
        gap: 8,
      }}
    >
      {currentStep > 1 && !isResult ? (
        <TouchableOpacity
          onPress={onBack}
          activeOpacity={0.7}
          style={{
            paddingVertical: 13,
            paddingHorizontal: 16,
            borderRadius: theme.rSm,
            borderWidth: 1.5,
            borderColor: theme.border,
            backgroundColor: theme.white,
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <Text style={{ fontSize: 14, fontWeight: "600", color: theme.inkMid }}>← Voltar</Text>
        </TouchableOpacity>
      ) : null}

      <TouchableOpacity
        onPress={isResult ? onReset : onNext}
        disabled={isLoading}
        activeOpacity={isLoading ? 1 : 0.8}
        style={{
          flex: 1,
          paddingVertical: 13,
          borderRadius: theme.rSm,
          backgroundColor: isResult ? theme.ink : theme.blue,
          justifyContent: "center",
          alignItems: "center",
          opacity: isLoading ? 0.7 : 1,
        }}
      >
        <Text style={{ fontSize: 14, fontWeight: "600", color: "white" }}>{nextLabel}</Text>
      </TouchableOpacity>
    </View>
  );
}
