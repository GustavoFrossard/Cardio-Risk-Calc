import { ETAPAS_WIZARD } from "../types";

function ThemeToggle({ theme, onToggle }) {
  const isDark = theme === "dark";
  return (
    <button
      type="button"
      onClick={onToggle}
      title={isDark ? "Mudar para modo claro" : "Mudar para modo escuro"}
      aria-label={isDark ? "Mudar para modo claro" : "Mudar para modo escuro"}
      style={{
        width: 32,
        height: 32,
        borderRadius: 999,
        border: "1px solid var(--border)",
        background: "var(--bg)",
        color: "var(--ink-mid)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        flexShrink: 0,
        padding: 0,
        transition: "all 0.15s",
      }}
    >
      {isDark ? (
        // Sol
        <svg width={17} height={17} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <circle cx={12} cy={12} r={4} />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
        </svg>
      ) : (
        // Lua
        <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      )}
    </button>
  );
}

export function CabecalhoApp({ etapaAtual, maiorEtapa, onIrParaEtapa, theme, onToggleTheme }) {
  const etapa = ETAPAS_WIZARD[etapaAtual - 1];

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
          {etapaAtual} / {ETAPAS_WIZARD.length}
        </div>
        <ThemeToggle theme={theme} onToggle={onToggleTheme} />
      </div>

      {/* Barras de progresso — clicáveis para etapas já visitadas */}
      <div style={{ display: "flex", gap: 4, marginBottom: -1 }}>
        {ETAPAS_WIZARD.map((s) => {
          const isVisited = s.id < etapaAtual && s.id < 4;
          const isCurrent = s.id === etapaAtual;
          const isClickable = isVisited && onIrParaEtapa;

          return (
            <div
              key={s.id}
              title={isClickable ? `Ir para: ${s.titulo}` : undefined}
              onClick={isClickable ? () => onIrParaEtapa(s.id) : undefined}
              style={{
                height: isClickable ? 4 : 2,
                flex: 1,
                borderRadius: 3,
                background: isCurrent
                  ? "var(--blue)"
                  : s.id < etapaAtual
                  ? "rgba(91,148,245,0.55)"
                  : "var(--border)",
                transition: "background 0.3s, height 0.2s",
                cursor: isClickable ? "pointer" : "default",
              }}
            />
          );
        })}
      </div>

      {/* Linha de título da etapa com bolhas clicáveis */}
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
          {etapaAtual}
        </div>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-mid)" }}>
          {etapa?.titulo}
        </div>

        {/* Breadcrumb para etapas visitadas */}
        {maiorEtapa > 1 && etapaAtual < maiorEtapa && (
          <div style={{ display: "flex", gap: 4, marginLeft: "auto" }}>
            {ETAPAS_WIZARD.slice(0, maiorEtapa - 1).filter(s => s.id !== etapaAtual && s.id < 4).map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => onIrParaEtapa?.(s.id)}
                title={s.titulo}
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: "50%",
                  border: "1.5px solid var(--border)",
                  background: "var(--bg)",
                  color: "var(--ink-muted)",
                  fontSize: 10,
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {s.id}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
