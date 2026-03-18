import React from "react";

// ─── Toggle Switch ────────────────────────────────────────────────────────────

interface ToggleProps {
  checked: boolean;
  onChange: (val: boolean) => void;
}

export function Toggle({ checked, onChange }: ToggleProps) {
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

// ─── Toggle Row ───────────────────────────────────────────────────────────────

interface ToggleRowProps {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (val: boolean) => void;
  badge?: string; // e.g. "+1"
  isLast?: boolean;
}

export function ToggleRow({ label, description, checked, onChange, badge, isLast }: ToggleRowProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: isLast ? "11px 0 0" : "11px 0",
        borderBottom: isLast ? "none" : "1px solid var(--border)",
        gap: 10,
      }}
    >
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: "var(--ink)", lineHeight: 1.3 }}>
          {label}
        </div>
        {description && (
          <div style={{ fontSize: 11, color: "var(--ink-muted)", marginTop: 2 }}>
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
  );
}

// ─── Card ─────────────────────────────────────────────────────────────────────

interface CardProps {
  icon?: string;
  title?: string;
  children: React.ReactNode;
  style?: React.CSSProperties;
}

export function Card({ icon, title, children, style }: CardProps) {
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

interface FieldProps {
  label: string;
  children: React.ReactNode;
  style?: React.CSSProperties;
}

export function Field({ label, children, style }: FieldProps) {
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

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  unit?: string;
}

export function Input({ unit, style, ...props }: InputProps) {
  const inputStyle: React.CSSProperties = {
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

// ─── Select ───────────────────────────────────────────────────────────────────

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      style={{
        width: "100%",
        border: "1.5px solid var(--border)",
        borderRadius: "var(--r-sm)",
        padding: "10px 13px",
        fontFamily: "'Outfit', sans-serif",
        fontSize: 14,
        color: props.value ? "var(--ink)" : "#C8CBD4",
        background: "var(--white)",
        outline: "none",
        WebkitAppearance: "none",
        appearance: "none",
        cursor: "pointer",
      }}
      {...props}
    />
  );
}

// ─── Chip Group ───────────────────────────────────────────────────────────────

interface ChipOption<T extends string> {
  value: T;
  label: string;
}

interface ChipGroupProps<T extends string> {
  options: ChipOption<T>[];
  value: T | "";
  onChange: (val: T) => void;
}

export function ChipGroup<T extends string>({ options, value, onChange }: ChipGroupProps<T>) {
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          style={{
            padding: "7px 14px",
            borderRadius: 999,
            border: `1.5px solid ${value === opt.value ? "var(--blue)" : "var(--border)"}`,
            fontSize: 12,
            fontWeight: 500,
            color: value === opt.value ? "white" : "var(--ink-muted)",
            background: value === opt.value ? "var(--blue)" : "var(--white)",
            cursor: "pointer",
            transition: "all 0.15s",
            fontFamily: "'Outfit', sans-serif",
          }}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

// ─── Info Box ─────────────────────────────────────────────────────────────────

interface InfoBoxProps {
  icon?: string;
  children: React.ReactNode;
}

export function InfoBox({ icon = "ℹ️", children }: InfoBoxProps) {
  return (
    <div
      style={{
        borderRadius: "var(--r-sm)",
        padding: "12px 14px",
        border: "1px solid #BDD3FB",
        background: "var(--blue-soft)",
        display: "flex",
        gap: 10,
        alignItems: "flex-start",
      }}
    >
      <span style={{ fontSize: 16, flexShrink: 0 }}>{icon}</span>
      <div style={{ fontSize: 12, color: "#1A3B7A", lineHeight: 1.55 }}>{children}</div>
    </div>
  );
}
