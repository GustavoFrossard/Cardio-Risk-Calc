export function TelaBoasVindas({ onStart }) {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        padding: "48px 28px",
        gap: 22,
      }}
    >
      <div
        style={{
          width: 72,
          height: 72,
          background: "var(--blue)",
          borderRadius: 20,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 8px 24px -8px var(--blue-mid)",
        }}
      >
        <svg width={38} height={38} viewBox="0 0 24 24" fill="none">
          <path
            d="M12 21C12 21 3 15.5 3 9C3 6.24 5.24 4 8 4C9.64 4 11.09 4.79 12 6.01C12.91 4.79 14.36 4 16 4C18.76 4 21 6.24 21 9C21 15.5 12 21 12 21Z"
            fill="white"
          />
        </svg>
      </div>

      <h1 style={{ fontSize: 26, fontWeight: 700, color: "var(--ink)", letterSpacing: -0.3 }}>
        CardioRisk Periop
      </h1>

      <button
        type="button"
        onClick={onStart}
        style={{
          marginTop: 10,
          padding: "14px 32px",
          borderRadius: "var(--r-sm)",
          border: "none",
          background: "var(--blue)",
          color: "white",
          fontFamily: "'Outfit', sans-serif",
          fontSize: 15,
          fontWeight: 600,
          cursor: "pointer",
          transition: "all 0.15s",
        }}
      >
        Iniciar Avaliação →
      </button>

      <div style={{ fontSize: 11, color: "var(--ink-muted)", marginTop: 24, maxWidth: 340, lineHeight: 1.5 }}>
        Ferramenta de suporte clínico. Não substitui o julgamento médico individualizado.
      </div>
    </div>
  );
}
