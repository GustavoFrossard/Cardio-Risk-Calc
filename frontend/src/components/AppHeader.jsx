import { WIZARD_STEPS } from "../types";

export function AppHeader({ currentStep }) {
  const step = WIZARD_STEPS[currentStep - 1];

  return (
    <div
      style={{
        background: "var(--white)",
        padding: "52px 20px 0",
        borderBottom: "1px solid var(--border)",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
        <div
          style={{
            width: 34,
            height: 34,
            background: "var(--blue)",
            borderRadius: 10,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <svg width={18} height={18} viewBox="0 0 24 24" fill="none">
            <path
              d="M12 21C12 21 3 15.5 3 9C3 6.24 5.24 4 8 4C9.64 4 11.09 4.79 12 6.01C12.91 4.79 14.36 4 16 4C18.76 4 21 6.24 21 9C21 15.5 12 21 12 21Z"
              fill="white"
            />
          </svg>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--ink)" }}>CardioRisk Periop</div>
          <div style={{ fontSize: 11, color: "var(--ink-muted)" }}>AHA/ACC 2014 · Índice de Lee</div>
        </div>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11,
            color: "var(--ink-muted)",
            background: "var(--bg)",
            padding: "4px 10px",
            borderRadius: 999,
            border: "1px solid var(--border)",
          }}
        >
          {currentStep} / {WIZARD_STEPS.length}
        </div>
      </div>

      <div style={{ display: "flex", gap: 4, marginBottom: -1 }}>
        {WIZARD_STEPS.map((s) => (
          <div
            key={s.id}
            style={{
              height: 2,
              flex: 1,
              borderRadius: 2,
              background:
                s.id === currentStep
                  ? "var(--blue)"
                  : s.id < currentStep
                  ? "rgba(91,148,245,0.5)"
                  : "var(--border)",
              transition: "background 0.3s",
            }}
          />
        ))}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 0 12px" }}>
        <div
          style={{
            width: 22,
            height: 22,
            borderRadius: "50%",
            background: "var(--blue)",
            color: "white",
            fontSize: 11,
            fontWeight: 700,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          {currentStep}
        </div>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-mid)" }}>
          {step?.title}
        </div>
      </div>
    </div>
  );
}
