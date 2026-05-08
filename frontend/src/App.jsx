import { useAssistente } from "./hooks/useWizard";
import { CabecalhoApp } from "./components/AppHeader";
import { BarraInferior } from "./components/BottomBar";
import { EtapaDadosPaciente } from "./components/steps/StepPatientData";
import { EtapaCirurgia } from "./components/steps/StepSurgery";
import { EtapaRCRI } from "./components/steps/StepRCRI";
import { EtapaResultado } from "./components/steps/StepResult";

export default function App() {
  const { currentStep, totalSteps, formData, result, isLoading, error, updateField, goNext, goBack, reset } =
    useAssistente();

  return (
    <div
      style={{
        width: "100%",
        maxWidth: 420,
        minHeight: "100vh",
        background: "var(--bg)",
        position: "relative",
        margin: "0 auto",
      }}
    >
      <CabecalhoApp currentStep={currentStep} />

      <div
        style={{
          padding: "16px 16px 110px",
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}
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

        {error && (
          <div
            style={{
              background: "var(--red-soft)",
              border: "1px solid #F5B0AA",
              borderRadius: "var(--r-sm)",
              padding: "12px 16px",
              fontSize: 13,
              color: "var(--red)",
              lineHeight: 1.5,
            }}
          >
            <strong>Erro:</strong> {error}
          </div>
        )}
      </div>

      <BarraInferior
        currentStep={currentStep}
        totalSteps={totalSteps}
        isLoading={isLoading}
        onBack={goBack}
        onNext={goNext}
        onReset={reset}
      />
    </div>
  );
}
