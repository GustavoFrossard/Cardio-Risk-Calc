import {
  View,
  Text,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { registerRootComponent } from "expo";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { useAssistente } from "./src/hooks/useWizard";
import { CabecalhoApp } from "./src/components/AppHeader";
import { BarraInferior } from "./src/components/BottomBar";
import { EtapaDadosPaciente } from "./src/components/steps/StepPatientData";
import { EtapaCirurgia } from "./src/components/steps/StepSurgery";
import { EtapaRCRI } from "./src/components/steps/StepRCRI";
import { EtapaResultado } from "./src/components/steps/StepResult";
import { theme } from "./src/theme";

export default function App() {
  const {
    currentStep,
    totalSteps,
    formData,
    result,
    isLoading,
    error,
    updateField,
    goNext,
    goBack,
    reset,
  } = useAssistente();

  return (
    <SafeAreaProvider>
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.bg }}>
      <StatusBar style="dark" />

      <CabecalhoApp currentStep={currentStep} />

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={0}
      >
        <ScrollView
          style={{ flex: 1 }}
          contentContainerStyle={{
            padding: 16,
            paddingBottom: 24,
            gap: 10,
          }}
          keyboardShouldPersistTaps="handled"
        >
          {currentStep === 1 && (
            <EtapaDadosPaciente data={formData} onChange={updateField} />
          )}
          {currentStep === 2 && (
            <EtapaCirurgia data={formData} onChange={updateField} />
          )}
          {currentStep === 3 && (
            <EtapaRCRI data={formData} onChange={updateField} />
          )}
          {currentStep === 4 && result && (
            <EtapaResultado result={result} data={formData} />
          )}

          {error ? (
            <View
              style={{
                backgroundColor: theme.redSoft,
                borderWidth: 1,
                borderColor: "#F5B0AA",
                borderRadius: theme.rSm,
                padding: 12,
              }}
            >
              <Text style={{ fontSize: 13, color: theme.red, lineHeight: 19 }}>
                <Text style={{ fontWeight: "bold" }}>Erro: </Text>
                {error}
              </Text>
            </View>
          ) : null}
        </ScrollView>
      </KeyboardAvoidingView>

      <BarraInferior
        currentStep={currentStep}
        totalSteps={totalSteps}
        isLoading={isLoading}
        onBack={goBack}
        onNext={goNext}
        onReset={reset}
      />
    </SafeAreaView>
    </SafeAreaProvider>
  );
}

registerRootComponent(App);
