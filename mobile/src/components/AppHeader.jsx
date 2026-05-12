import { View, Text } from "react-native";
import { WIZARD_STEPS } from "../types";
import { theme } from "../theme";

export function CabecalhoApp({ currentStep }) {
  const step = WIZARD_STEPS[currentStep - 1];

  return (
    <View
      style={{
        backgroundColor: theme.white,
        paddingTop: 12,
        paddingHorizontal: 16,
        paddingBottom: 0,
        borderBottomWidth: 1,
        borderBottomColor: theme.border,
      }}
    >
      {/* Title row */}
      <View style={{ flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 12 }}>
        <View
          style={{
            width: 34,
            height: 34,
            backgroundColor: theme.blue,
            borderRadius: 10,
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <Text style={{ fontSize: 18, lineHeight: 22 }}>❤️</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={{ fontSize: 13, fontWeight: "600", color: theme.ink }}>
            CardioRisk Periop
          </Text>
          <Text style={{ fontSize: 11, color: theme.inkMuted }}>
            AHA/ACC 2014 · Índice de Lee
          </Text>
        </View>
        <View
          style={{
            borderRadius: 999,
            borderWidth: 1,
            borderColor: theme.border,
            backgroundColor: theme.bg,
            paddingHorizontal: 10,
            paddingVertical: 4,
          }}
        >
          <Text
            style={{
              fontFamily: "monospace",
              fontSize: 11,
              color: theme.inkMuted,
            }}
          >
            {currentStep} / {WIZARD_STEPS.length}
          </Text>
        </View>
      </View>

      {/* Progress bars */}
      <View style={{ flexDirection: "row", gap: 4 }}>
        {WIZARD_STEPS.map((s) => (
          <View
            key={s.id}
            style={{
              height: 2,
              flex: 1,
              borderRadius: 2,
              backgroundColor:
                s.id === currentStep
                  ? theme.blue
                  : s.id < currentStep
                  ? theme.blueMid
                  : theme.border,
            }}
          />
        ))}
      </View>

      {/* Step title */}
      <View style={{ flexDirection: "row", alignItems: "center", gap: 8, paddingVertical: 10 }}>
        <View
          style={{
            width: 22,
            height: 22,
            borderRadius: 11,
            backgroundColor: theme.blue,
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <Text style={{ fontSize: 11, fontWeight: "700", color: "white" }}>{currentStep}</Text>
        </View>
        <Text style={{ fontSize: 13, fontWeight: "600", color: theme.inkMid }}>
          {step?.title}
        </Text>
      </View>
    </View>
  );
}
