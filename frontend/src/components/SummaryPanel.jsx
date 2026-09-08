import { resumirPaciente, resumirCirurgia, resumirComorbidades, resumirMedicamentos } from "../utils/resumo";
import { Eyebrow } from "./ui";

function Chip({ children, tone = "blue" }) {
  const tones = {
    blue: { color: "var(--blue)", background: "var(--blue-soft)" },
    amber: { color: "var(--amber)", background: "var(--amber-soft)" },
  };
  const t = tones[tone];
  return (
    <span
      style={{
        fontSize: 12,
        fontWeight: 600,
        color: t.color,
        background: t.background,
        borderRadius: 999,
        padding: "5px 11px",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </span>
  );
}

function Secao({ titulo, children }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <Eyebrow style={{ padding: 0, marginBottom: 8 }}>{titulo}</Eyebrow>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>{children}</div>
    </div>
  );
}

export function PainelResumo({ dados }) {
  const paciente = resumirPaciente(dados);
  const cirurgia = resumirCirurgia(dados);
  const comorbidades = resumirComorbidades(dados);
  const medicamentos = resumirMedicamentos(dados);

  const camposChave = [paciente.idade != null, cirurgia.definida, dados.mets != null];
  const preenchidos = camposChave.filter(Boolean).length;

  return (
    <div style={{ width: 300, display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ background: "var(--white)", border: "1px solid var(--border)", borderRadius: "var(--r)", padding: 18 }}>
        <Eyebrow style={{ padding: 0, marginBottom: 14 }}>Resumo da avaliação</Eyebrow>

        <Secao titulo="Paciente">
          {paciente.idade != null ? <Chip>{paciente.idade} anos</Chip> : <Chip tone="amber">Idade não informada</Chip>}
          {paciente.mets != null && <Chip>{paciente.mets} METs</Chip>}
        </Secao>

        <Secao titulo="Comorbidades">
          {comorbidades.length > 0 ? (
            comorbidades.map((c) => <Chip key={c}>{c}</Chip>)
          ) : (
            <span style={{ fontSize: 12, color: "var(--ink-muted)" }}>Nenhuma marcada</span>
          )}
        </Secao>

        {medicamentos.length > 0 && (
          <Secao titulo="Medicamentos">
            {medicamentos.map((m) => (
              <Chip key={m}>{m}</Chip>
            ))}
          </Secao>
        )}

        <Secao titulo="Cirurgia">
          {cirurgia.definida ? <Chip>{cirurgia.rotulo}</Chip> : <Chip tone="amber">Ainda não definida</Chip>}
        </Secao>

        <div style={{ height: 1, background: "var(--border)", margin: "14px 0" }} />

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <svg width={15} height={15} viewBox="0 0 24 24" fill="none">
            <circle cx={12} cy={12} r={10} stroke="var(--ink-muted)" strokeWidth={2} />
            <path d="M12 8v4M12 16h.01" stroke="var(--ink-muted)" strokeWidth={2} strokeLinecap="round" />
          </svg>
          <span style={{ fontSize: 12, color: "var(--ink-muted)" }}>
            {preenchidos} de {camposChave.length} campos-chave preenchidos
          </span>
        </div>
      </div>
    </div>
  );
}
