import { useEffect, useState } from "react";
import { useAssistente } from "./hooks/useWizard";
import { CabecalhoApp } from "./components/AppHeader";
import { BarraInferior } from "./components/BottomBar";
import { EtapaDadosPaciente } from "./components/steps/StepPatientData";
import { EtapaCirurgia } from "./components/steps/StepSurgery";
import { EtapaRCRI } from "./components/steps/StepRCRI";
import { EtapaResultado } from "./components/steps/StepResult";

export default function App() {
  const {
    currentStep,
    totalSteps,
    highestStep,
    hasSavedData,
    formData,
    result,
    isLoading,
    isAnalyzing,
    nlpResult,
    error,
    updateField,
    analyzeClinicalText,
    goNext,
    goBack,
    goToStep,
    resumeSaved,
    reset,
  } = useAssistente();

  const [showResumeModal, setShowResumeModal] = useState(hasSavedData);
  const [maxWidth, setMaxWidth] = useState(() => window.innerWidth >= 768 ? 640 : 420);

  useEffect(() => {
    const onResize = () => setMaxWidth(window.innerWidth >= 768 ? 640 : 420);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }, [currentStep]);

  // Keyboard shortcuts (desktop)
  useEffect(() => {
    const onKey = (e) => {
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (showResumeModal) return;
      if (e.key === "Enter" || e.key === "ArrowRight") {
        e.preventDefault();
        goNext();
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        goBack();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [goNext, goBack, showResumeModal]);

  return (
    <div
      style={{
        width: "100%",
        maxWidth: maxWidth,
        minHeight: "100vh",
        background: "var(--bg)",
        position: "relative",
        margin: "0 auto",
        transition: "max-width 0.3s ease",
      }}
    >
      {/* Resume modal */}
      {showResumeModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.55)",
            zIndex: 300,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 20,
          }}
        >
          <div
            style={{
              background: "var(--white)",
              borderRadius: "var(--r)",
              padding: 24,
              maxWidth: 360,
              width: "100%",
              boxShadow: "0 8px 32px rgba(0,0,0,0.2)",
            }}
          >
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                background: "var(--blue-soft)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: 14,
              }}
            >
              <svg width={20} height={20} viewBox="0 0 24 24" fill="none">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z" fill="var(--blue)" />
              </svg>
            </div>
            <div style={{ fontSize: 16, fontWeight: 700, color: "var(--ink)", marginBottom: 8 }}>
              Retomar avaliação?
            </div>
            <div style={{ fontSize: 13, color: "var(--ink-mid)", marginBottom: 22, lineHeight: 1.55 }}>
              Há uma avaliação em andamento salva. Deseja retomá-la de onde parou ou iniciar uma nova?
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                style={{
                  flex: 1,
                  padding: "11px 0",
                  borderRadius: "var(--r-sm)",
                  border: "1.5px solid var(--border)",
                  background: "var(--white)",
                  color: "var(--ink-mid)",
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
                onClick={() => { reset(); setShowResumeModal(false); }}
              >
                Nova avaliação
              </button>
              <button
                style={{
                  flex: 1,
                  padding: "11px 0",
                  borderRadius: "var(--r-sm)",
                  border: "none",
                  background: "var(--blue)",
                  color: "white",
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
                onClick={() => { resumeSaved(); setShowResumeModal(false); }}
              >
                Retomar →
              </button>
            </div>
          </div>
        </div>
      )}

      <CabecalhoApp
        currentStep={currentStep}
        highestStep={highestStep}
        onGoToStep={goToStep}
      />

      <div
        style={{
          padding: "16px 16px 110px",
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}
      >
        {currentStep === 1 && (
          <EtapaDadosPaciente
            data={formData}
            onChange={updateField}
            onAnalyzeClinicalText={analyzeClinicalText}
            isAnalyzing={isAnalyzing}
            nlpResult={nlpResult}
          />
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
