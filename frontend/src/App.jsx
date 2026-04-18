import { useWizard } from "./hooks/useWizard";
import { AppHeader } from "./components/AppHeader";
import { BottomBar } from "./components/BottomBar";
import { StepPatientData } from "./components/steps/StepPatientData";
import { StepSurgery } from "./components/steps/StepSurgery";
import { StepRCRI } from "./components/steps/StepRCRI";
import { StepResult } from "./components/steps/StepResult";

export default function App() {
  const { currentStep, totalSteps, formData, result, isLoading, error, updateField, goNext, goBack, reset } =
    useWizard();

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
      <AppHeader currentStep={currentStep} />

      <div
        style={{
          padding: "16px 16px 110px",
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}
      >
        {currentStep === 1 && (
          <StepPatientData data={formData} onChange={updateField} />
        )}
        {currentStep === 2 && (
          <StepSurgery data={formData} onChange={updateField} />
        )}
        {currentStep === 3 && (
          <StepRCRI data={formData} onChange={updateField} />
        )}
        {currentStep === 4 && result && (
          <StepResult result={result} data={formData} />
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

      <BottomBar
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
