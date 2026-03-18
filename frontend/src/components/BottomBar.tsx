interface Props {
  currentStep: number;
  totalSteps: number;
  isLoading: boolean;
  onBack: () => void;
  onNext: () => void;
  onReset: () => void;
}

export function BottomBar({ currentStep, totalSteps, isLoading, onBack, onNext, onReset }: Props) {
  const isResult = currentStep === totalSteps;
  const isLastInput = currentStep === totalSteps - 1;

  const nextLabel = isLoading
    ? "Calculando..."
    : isResult
    ? "Nova Avaliação"
    : isLastInput
    ? "Calcular Risco"
    : "Próximo →";

  const nextStyle: React.CSSProperties = {
    flex: 1,
    padding: 13,
    borderRadius: "var(--r-sm)",
    fontFamily: "'Outfit', sans-serif",
    fontSize: 14,
    fontWeight: 600,
    border: "none",
    cursor: isLoading ? "not-allowed" : "pointer",
    transition: "all 0.15s",
    background: isResult ? "var(--ink)" : "var(--blue)",
    color: "white",
    opacity: isLoading ? 0.7 : 1,
  };

  const backStyle: React.CSSProperties = {
    flex: "0 0 auto",
    padding: "13px 16px",
    borderRadius: "var(--r-sm)",
    fontFamily: "'Outfit', sans-serif",
    fontSize: 14,
    fontWeight: 600,
    border: "1.5px solid var(--border)",
    cursor: "pointer",
    transition: "all 0.15s",
    background: "var(--white)",
    color: "var(--ink-mid)",
  };

  return (
    <div
      style={{
        position: "fixed",
        bottom: 0,
        left: "50%",
        transform: "translateX(-50%)",
        width: "100%",
        maxWidth: 420,
        background: "rgba(255,255,255,0.94)",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        padding: "12px 16px 28px",
        borderTop: "1px solid var(--border)",
        display: "flex",
        gap: 8,
        zIndex: 100,
      }}
    >
      {currentStep > 1 && !isResult && (
        <button style={backStyle} onClick={onBack} type="button">
          ← Voltar
        </button>
      )}
      <button
        style={nextStyle}
        onClick={isResult ? onReset : onNext}
        disabled={isLoading}
        type="button"
      >
        {nextLabel}
      </button>
    </div>
  );
}
