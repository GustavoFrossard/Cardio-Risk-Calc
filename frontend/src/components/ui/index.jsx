import { useState } from "react";
import { Info } from "lucide-react";

// ─── Toggle ───────────────────────────────────────────────────────────────────

export function Toggle({ checked, onChange }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      style={{
        width: 40,
        height: 23,
        borderRadius: 999,
        background: checked ? "var(--blue)" : "var(--border)",
        border: "none",
        position: "relative",
        cursor: "pointer",
        flexShrink: 0,
        transition: "background 0.2s",
      }}
    >
      <span
        style={{
          position: "absolute",
          width: 17,
          height: 17,
          background: "white",
          borderRadius: "50%",
          top: 3,
          left: 3,
          transition: "transform 0.2s",
          transform: checked ? "translateX(17px)" : "translateX(0)",
          boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
          display: "block",
        }}
      />
    </button>
  );
}

// ─── ToggleRow ────────────────────────────────────────────────────────────────

export function ToggleRow({ label, description, checked, onChange, badge, isLast }) {
  const [descOpen, setDescOpen] = useState(false);

  return (
    <div
      style={{
        padding: isLast ? "11px 0 0" : "11px 0",
        borderBottom: isLast ? "none" : "1px solid var(--border)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 10,
        }}
      >
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <span style={{ fontSize: 13, fontWeight: 500, color: "var(--ink)", lineHeight: 1.3 }}>
              {label}
            </span>
            {description && (
              <button
                type="button"
                onClick={() => setDescOpen((v) => !v)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: "0 2px",
                  display: "inline-flex",
                  color: descOpen ? "var(--blue)" : "var(--ink-muted)",
                  flexShrink: 0,
                }}
                title={descOpen ? "Ocultar detalhe" : "Ver detalhe"}
              >
                <Info size={13} strokeWidth={2} />
              </button>
            )}
          </div>
          {description && descOpen && (
            <div
              style={{
                fontSize: 11,
                color: "var(--ink-muted)",
                marginTop: 3,
                lineHeight: 1.4,
                paddingRight: 4,
              }}
            >
              {description}
            </div>
          )}
        </div>
        {badge && (
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: "var(--blue)",
              fontWeight: 500,
              flexShrink: 0,
              background: "var(--blue-soft)",
              padding: "2px 7px",
              borderRadius: 4,
            }}
          >
            {badge}
          </span>
        )}
        <Toggle checked={checked} onChange={onChange} />
      </div>
    </div>
  );
}

// ─── Card ─────────────────────────────────────────────────────────────────────

export function Card({ icon, title, children, style }) {
  return (
    <div
      style={{
        background: "var(--white)",
        borderRadius: "var(--r)",
        padding: 16,
        border: "1px solid var(--border)",
        boxShadow: "0 1px 4px rgba(13,17,23,0.06)",
        ...style,
      }}
    >
      {(icon || title) && (
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
          {icon && (
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: 8,
                background: "var(--blue-soft)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 13,
                flexShrink: 0,
              }}
            >
              {icon}
            </div>
          )}
          {title && (
            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--ink)" }}>
              {title}
            </span>
          )}
        </div>
      )}
      {children}
    </div>
  );
}

// ─── Field ────────────────────────────────────────────────────────────────────

export function Field({ label, children, style }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 5, ...style }}>
      <label
        style={{
          fontSize: 11,
          fontWeight: 500,
          color: "var(--ink-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
        }}
      >
        {label}
      </label>
      {children}
    </div>
  );
}

// ─── Input ────────────────────────────────────────────────────────────────────

export function Input({ unit, style, ...props }) {
  const inputStyle = {
    width: "100%",
    border: "1.5px solid var(--border)",
    borderRadius: "var(--r-sm)",
    padding: unit ? "10px 52px 10px 13px" : "10px 13px",
    fontFamily: "'Outfit', sans-serif",
    fontSize: 14,
    color: "var(--ink)",
    background: "var(--white)",
    outline: "none",
    WebkitAppearance: "none",
    ...style,
  };

  if (!unit) return <input style={inputStyle} {...props} />;

  return (
    <div style={{ position: "relative" }}>
      <input style={inputStyle} {...props} />
      <span
        style={{
          position: "absolute",
          right: 12,
          top: "50%",
          transform: "translateY(-50%)",
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          color: "var(--ink-muted)",
          pointerEvents: "none",
          fontWeight: 500,
        }}
      >
        {unit}
      </span>
    </div>
  );
}

// ─── AgeInput — numeric input with − / + stepper buttons ─────────────────────

export function AgeInput({ value, onChange, min = 0, max = 120 }) {
  const num = value != null && value !== "" ? Number(value) : null;

  const decrement = () => {
    const next = num != null ? Math.max(num - 1, min) : max;
    onChange(next);
  };

  const increment = () => {
    const next = num != null ? Math.min(num + 1, max) : min;
    onChange(next);
  };

  const btnStyle = {
    width: 38,
    height: 42,
    border: "1.5px solid var(--border)",
    background: "var(--bg)",
    color: "var(--ink-mid)",
    fontSize: 18,
    fontWeight: 500,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    userSelect: "none",
    WebkitUserSelect: "none",
    lineHeight: 1,
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
      <button
        type="button"
        onClick={decrement}
        style={{ ...btnStyle, borderRadius: "var(--r-sm) 0 0 var(--r-sm)", borderRight: "none" }}
      >
        −
      </button>
      <input
        type="number"
        value={value ?? ""}
        min={min}
        max={max}
        onChange={(e) => {
          if (!e.target.value) { onChange(undefined); return; }
          const v = Math.min(Math.max(Number(e.target.value), min), max);
          onChange(isNaN(v) ? undefined : v);
        }}
        style={{
          flex: 1,
          minWidth: 0,
          border: "1.5px solid var(--border)",
          borderLeft: "none",
          borderRight: "none",
          borderRadius: 0,
          padding: "10px 8px",
          fontFamily: "'Outfit', sans-serif",
          fontSize: 16,
          fontWeight: 600,
          color: "var(--ink)",
          background: "var(--white)",
          outline: "none",
          textAlign: "center",
          WebkitAppearance: "none",
          MozAppearance: "textfield",
        }}
        placeholder="—"
      />
      <span
        style={{
          padding: "0 10px",
          background: "var(--white)",
          border: "1.5px solid var(--border)",
          borderLeft: "none",
          borderRight: "none",
          height: 42,
          display: "flex",
          alignItems: "center",
          fontSize: 10,
          fontWeight: 500,
          color: "var(--ink-muted)",
          fontFamily: "'JetBrains Mono', monospace",
          flexShrink: 0,
        }}
      >
        anos
      </span>
      <button
        type="button"
        onClick={increment}
        style={{ ...btnStyle, borderRadius: "0 var(--r-sm) var(--r-sm) 0", borderLeft: "none" }}
      >
        +
      </button>
    </div>
  );
}

// ─── Select (native) ──────────────────────────────────────────────────────────

export function Select(props) {
  return (
    <select
      style={{
        width: "100%",
        border: "1.5px solid var(--border)",
        borderRadius: "var(--r-sm)",
        padding: "10px 36px 10px 13px",
        fontFamily: "'Outfit', sans-serif",
        fontSize: 14,
        color: props.value ? "var(--ink)" : "#C8CBD4",
        background: "var(--white)",
        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238B909A' stroke-width='1.5' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E")`,
        backgroundRepeat: "no-repeat",
        backgroundPosition: "right 12px center",
        outline: "none",
        WebkitAppearance: "none",
        appearance: "none",
        cursor: "pointer",
        minHeight: 44,
      }}
      {...props}
    />
  );
}

// ─── SearchSelect — modal picker with search ──────────────────────────────────

export function SearchSelect({ value, onChange, options, placeholder = "Selecione..." }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const selectedLabel = options?.find((o) => !o.ehCabecalho && o.valor === value)?.rotulo ?? null;

  const filtered = query.trim()
    ? options.filter((o) => o.ehCabecalho || o.rotulo.toLowerCase().includes(query.toLowerCase()))
    : options;

  // Remove orphan headers (header followed by another header or end)
  const displayList = filtered.filter((item, idx) => {
    if (!item.ehCabecalho) return true;
    const next = filtered[idx + 1];
    return next && !next.ehCabecalho;
  });

  return (
    <>
      <button
        type="button"
        onClick={() => { setQuery(""); setOpen(true); }}
        style={{
          width: "100%",
          border: "1.5px solid var(--border)",
          borderRadius: "var(--r-sm)",
          background: "var(--white)",
          padding: "10px 36px 10px 13px",
          fontSize: 14,
          color: selectedLabel ? "var(--ink)" : "#C8CBD4",
          textAlign: "left",
          cursor: "pointer",
          minHeight: 44,
          position: "relative",
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238B909A' stroke-width='1.5' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E")`,
          backgroundRepeat: "no-repeat",
          backgroundPosition: "right 12px center",
          fontFamily: "'Outfit', sans-serif",
          overflow: "hidden",
          whiteSpace: "nowrap",
          textOverflow: "ellipsis",
        }}
      >
        {selectedLabel ?? placeholder}
      </button>

      {open && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 200,
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "center",
            background: "rgba(0,0,0,0.45)",
          }}
          onClick={(e) => { if (e.target === e.currentTarget) setOpen(false); }}
        >
          <div
            style={{
              background: "var(--white)",
              borderRadius: "20px 20px 0 0",
              width: "100%",
              maxWidth: 640,
              maxHeight: "75vh",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "16px 16px 10px",
                borderBottom: "1px solid var(--border)",
                flexShrink: 0,
              }}
            >
              <span style={{ fontSize: 15, fontWeight: 600, color: "var(--ink)" }}>
                Selecionar procedimento
              </span>
              <button
                type="button"
                onClick={() => setOpen(false)}
                style={{ background: "none", border: "none", color: "var(--blue)", fontSize: 15, fontWeight: 500, cursor: "pointer" }}
              >
                Fechar
              </button>
            </div>

            {/* Search */}
            <div style={{ padding: "10px 16px 6px", flexShrink: 0 }}>
              <div style={{ position: "relative" }}>
                <svg
                  style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--ink-muted)", pointerEvents: "none" }}
                  width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round"
                >
                  <circle cx={11} cy={11} r={8} /><path d="m21 21-4.35-4.35" />
                </svg>
                <input
                  autoFocus
                  type="text"
                  placeholder="Buscar procedimento..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  style={{
                    width: "100%",
                    border: "1.5px solid var(--border)",
                    borderRadius: "var(--r-sm)",
                    padding: "9px 13px 9px 32px",
                    fontFamily: "'Outfit', sans-serif",
                    fontSize: 14,
                    color: "var(--ink)",
                    background: "var(--bg)",
                    outline: "none",
                  }}
                />
              </div>
            </div>

            {/* List */}
            <div style={{ overflowY: "auto", flex: 1, paddingBottom: 24 }}>
              {displayList.length === 0 && (
                <div style={{ padding: "24px 16px", textAlign: "center", fontSize: 13, color: "var(--ink-muted)" }}>
                  Nenhum procedimento encontrado
                </div>
              )}
              {displayList.map((item) => {
                if (item.ehCabecalho) {
                  return (
                    <div
                      key={item.valor}
                      style={{
                        padding: "8px 16px",
                        background: "var(--bg-soft)",
                        fontSize: 10,
                        fontWeight: 700,
                        color: "var(--ink-muted)",
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                      }}
                    >
                      {item.rotulo}
                    </div>
                  );
                }
                const isSelected = item.valor === value;
                return (
                  <button
                    key={item.valor}
                    type="button"
                    onClick={() => { onChange(item.valor); setOpen(false); }}
                    style={{
                      width: "100%",
                      padding: "13px 16px",
                      background: isSelected ? "var(--blue-soft)" : "transparent",
                      borderBottom: "1px solid var(--border)",
                      textAlign: "left",
                      fontSize: 13,
                      color: isSelected ? "var(--blue)" : "var(--ink)",
                      fontWeight: isSelected ? 500 : 400,
                      cursor: "pointer",
                      fontFamily: "'Outfit', sans-serif",
                      display: "block",
                    }}
                  >
                    {item.rotulo}
                    {isSelected && (
                      <span style={{ float: "right", color: "var(--blue)" }}>✓</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ─── ChipGroup ────────────────────────────────────────────────────────────────

export function ChipGroup({ options, value, onChange }) {
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {options.map((opt) => (
        <button
          key={opt.valor}
          type="button"
          onClick={() => onChange(opt.valor)}
          style={{
            padding: "7px 14px",
            borderRadius: 999,
            border: `1.5px solid ${value === opt.valor ? "var(--blue)" : "var(--border)"}`,
            fontSize: 12,
            fontWeight: 500,
            color: value === opt.valor ? "white" : "var(--ink-muted)",
            background: value === opt.valor ? "var(--blue)" : "var(--white)",
            cursor: "pointer",
            transition: "all 0.15s",
            fontFamily: "'Outfit', sans-serif",
          }}
        >
          {opt.rotulo}
        </button>
      ))}
    </div>
  );
}

// ─── InfoBox ──────────────────────────────────────────────────────────────────

export function InfoBox({ icon, children }) {
  const resolvedIcon = icon ?? <Info size={16} strokeWidth={2.2} color="var(--blue)" />;

  return (
    <div
      style={{
        borderRadius: "var(--r-sm)",
        padding: "12px 14px",
        border: "1px solid var(--blue-border)",
        background: "var(--blue-soft)",
        display: "flex",
        gap: 10,
        alignItems: "flex-start",
      }}
    >
      <span style={{ display: "inline-flex", flexShrink: 0 }}>{resolvedIcon}</span>
      <div style={{ fontSize: 12, color: "var(--blue)", lineHeight: 1.55 }}>{children}</div>
    </div>
  );
}

// ─── Accordion ────────────────────────────────────────────────────────────────

export function Accordion({ label, icon, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "0 2px 6px",
          background: "none",
          border: "none",
          cursor: "pointer",
          textAlign: "left",
          fontFamily: "'Outfit', sans-serif",
        }}
      >
        <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--ink-muted)", flex: 1 }}>
          {icon && <span style={{ marginRight: 4 }}>{icon}</span>}
          {label}
        </span>
        <span
          style={{
            color: "var(--ink-muted)",
            fontSize: 10,
            display: "inline-flex",
            transition: "transform 0.2s",
            transform: open ? "rotate(180deg)" : "none",
          }}
        >
          ▼
        </span>
      </button>
      {open && children}
    </div>
  );
}
