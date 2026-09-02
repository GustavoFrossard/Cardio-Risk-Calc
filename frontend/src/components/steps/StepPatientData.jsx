import { useEffect, useState } from "react";
import { Activity, BrainCircuit, CircleAlert, CircleCheck, Pill, Stethoscope, UserRound } from "lucide-react";
import { Card, Field, Input, AgeInput, ToggleRow, ChipGroup } from "../ui";
import { PERGUNTAS_FUNCIONAIS } from "../../types";

const SORTED_ACTIVITIES = [
  { rotulo: "Nenhuma atividade / acamado", mets: 1 },
  ...PERGUNTAS_FUNCIONAIS.slice().sort((a, b) => a.mets - b.mets),
];

const COMORBIDADES = [
  { key: "obesidade", rotulo: "Obesidade", descricao: "IMC ≥ 30" },
  { key: "ic_conhecida", rotulo: "IC conhecida ou suspeita", descricao: "Insuficiência cardíaca" },
  { key: "doenca_valvar_conhecida", rotulo: "Doença valvar conhecida ou suspeita", descricao: "Valvopatia diagnosticada ou suspeita clinicamente" },
  { key: "dac_conhecida", rotulo: "Doença coronariana conhecida ou suspeita", descricao: "Angina, IAM prévio, stent ou cirurgia de revascularização" },
];

const MEDICAMENTOS = [
  { key: "usa_aas", rotulo: "AAS (Ácido Acetilsalicílico)" },
  { key: "usa_clopidogrel", rotulo: "Clopidogrel" },
  { key: "usa_ticagrelor", rotulo: "Ticagrelor" },
  { key: "usa_prasugrel", rotulo: "Prasugrel" },
  { key: "usa_varfarina", rotulo: "Varfarina" },
];

const opcoesPrevencaoAas = [
  { valor: "primary", rotulo: "Primária" },
  { valor: "secondary", rotulo: "Secundária" },
];

const opcoesIndicacaoVarfarina = [
  { valor: "af", rotulo: "FA" },
  { valor: "vte", rotulo: "TEV" },
  { valor: "mechanical_valve", rotulo: "Prótese Mecânica" },
  { valor: "rheumatic", rotulo: "Valvar Reumática" },
];

const opcoesTempoTevVarfarina = [
  { valor: "recent", rotulo: "< 3 meses" },
  { valor: "3_12m", rotulo: "3–12 meses" },
  { valor: "over_12m", rotulo: "> 12 meses" },
];

const opcoesTrombofiliaVarfarina = [
  { valor: "severe", rotulo: "Grave" },
  { valor: "mild", rotulo: "Leve" },
  { valor: "none", rotulo: "Não" },
];

export function EtapaDadosPaciente({ data, onChange, onAnalisarTextoClinico, analisando, resultadoNlp }) {
  const [sliderIdx, setSliderIdx] = useState(() => {
    let best = 0;
    let minDiff = Infinity;
    for (let i = SORTED_ACTIVITIES.length - 1; i >= 0; i--) {
      const diff = Math.abs(SORTED_ACTIVITIES[i].mets - data.mets);
      if (diff < minDiff) { minDiff = diff; best = i; }
    }
    return best;
  });

  const currentActivity = SORTED_ACTIVITIES[sliderIdx];
  const mets = currentActivity.mets;
  const [clinicalText, setClinicalText] = useState("");
  const [textoInvalido, setTextoInvalido] = useState(false);

  const iconProps = { size: 16, strokeWidth: 2.2 };

  const TAMANHO_MINIMO_TEXTO = 5;

  const handleAnalyze = async () => {
    const text = clinicalText.trim();
    if (!text || !onAnalisarTextoClinico) return;
    if (text.length < TAMANHO_MINIMO_TEXTO) {
      setTextoInvalido(true);
      return;
    }
    setTextoInvalido(false);
    await onAnalisarTextoClinico(text);
  };

  useEffect(() => {
    let best = 0;
    let minDiff = Infinity;
    for (let i = SORTED_ACTIVITIES.length - 1; i >= 0; i--) {
      const diff = Math.abs(SORTED_ACTIVITIES[i].mets - (data.mets ?? 1));
      if (diff < minDiff) { minDiff = diff; best = i; }
    }
    setSliderIdx(best);
  }, [data.mets]);

  const sliderColor = mets >= 4 ? "var(--green)" : "var(--amber)";
  const sliderBg = mets >= 4 ? "var(--green-soft)" : "var(--amber-soft)";
  const sliderBorder = mets >= 4 ? "var(--green-border)" : "var(--amber-border)";

  return (
    <>
      <Card icon={<BrainCircuit {...iconProps} />} title="Pré-preenchimento por texto clínico">
        <Field label="Cole aqui o caso clínico">
          <textarea
            placeholder="Ex: Paciente de 67 anos com HAS e DM2 em insulinoterapia, antecedente de AVC, em programação de colecistectomia laparoscópica..."
            value={clinicalText}
            onChange={(e) => { setClinicalText(e.target.value); setTextoInvalido(false); }}
            rows={5}
            style={{
              width: "100%",
              border: "1.5px solid var(--border)",
              borderRadius: "var(--r-sm)",
              padding: "10px 13px",
              fontFamily: "'Outfit', sans-serif",
              fontSize: 14,
              color: "var(--ink)",
              background: "var(--white)",
              outline: "none",
              resize: "vertical",
              lineHeight: 1.45,
            }}
          />
        </Field>

        <button
          type="button"
          onClick={handleAnalyze}
          disabled={analisando || !clinicalText.trim()}
          style={{
            marginTop: 12,
            border: "none",
            borderRadius: "var(--r-sm)",
            background: analisando ? "#91A4CC" : "var(--blue)",
            color: "white",
            fontSize: 13,
            fontWeight: 600,
            padding: "10px 14px",
            cursor: analisando ? "not-allowed" : "pointer",
            width: "100%",
          }}
        >
          {analisando ? "Analisando caso clínico..." : "Analisar e auto-preencher"}
        </button>

        {textoInvalido && (
          <div
            style={{
              marginTop: 10,
              fontSize: 12,
              color: "var(--red)",
              lineHeight: 1.45,
            }}
          >
            Descreva o caso com mais detalhes (mínimo {TAMANHO_MINIMO_TEXTO} caracteres) para a análise funcionar.
          </div>
        )}

        {resultadoNlp && (
          <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
            <div
              style={{
                borderRadius: "var(--r-sm)",
                background: "var(--blue-soft)",
                border: "1px solid var(--blue-border)",
                padding: "10px 12px",
                fontSize: 12,
                color: "var(--blue)",
                lineHeight: 1.45,
              }}
            >
              <strong>{resultadoNlp?.summary?.autofill_count ?? 0}</strong> campos auto-preenchidos. Modelo:{" "}
              <strong>{resultadoNlp?.model?.name}</strong> ({resultadoNlp?.model?.status}).
            </div>

            {Array.isArray(resultadoNlp?.missing_critical) && resultadoNlp.missing_critical.length > 0 && (
              <div
                style={{
                  borderRadius: "var(--r-sm)",
                  background: "var(--amber-soft)",
                  border: "1px solid var(--amber-border)",
                  padding: "10px 12px",
                  fontSize: 12,
                  color: "var(--amber)",
                  lineHeight: 1.5,
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Informações críticas ausentes</div>
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {resultadoNlp.missing_critical.map((item) => (
                    <li key={item.campo}>{item.label}: {item.question}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Card>

      <Card icon={<UserRound {...iconProps} />} title="Identificação">
        <Field label="Nome / Identificador" style={{ marginBottom: 12 }}>
          <Input
            type="text"
            placeholder="Opcional"
            value={data.nome ?? ""}
            onChange={(e) => onChange("nome", e.target.value)}
          />
        </Field>
        <Field label="Idade">
          <AgeInput
            value={data.idade}
            onChange={(v) => onChange("idade", v)}
          />
        </Field>
      </Card>

      <Card icon={<Stethoscope {...iconProps} />} title="Comorbidades">
        {COMORBIDADES.map((item, i) => (
          <ToggleRow
            key={item.key}
            label={item.rotulo}
            description={item.descricao}
            checked={Boolean(data[item.key])}
            onChange={(val) => onChange(item.key, val)}
            isLast={i === COMORBIDADES.length - 1 && !data.ic_conhecida && !data.doenca_valvar_conhecida}
          />
        ))}

        {(data.ic_conhecida || data.doenca_valvar_conhecida) && (
          <div style={{ padding: "8px 0 12px 16px", display: "flex", flexDirection: "column", gap: 12, borderTop: "1px solid var(--border)" }}>
            <ToggleRow
              label="Ecocardiograma recente (< 6 meses)"
              checked={Boolean(data.eco_recente)}
              onChange={(val) => onChange("eco_recente", val)}
              isLast={false}
            />
            <ToggleRow
              label="Piora dos sintomas"
              checked={Boolean(data.piora_sintomas)}
              onChange={(val) => onChange("piora_sintomas", val)}
              isLast={true}
            />
          </div>
        )}
      </Card>

      <Card icon={<Pill {...iconProps} />} title="Medicamentos em Uso">
        {MEDICAMENTOS.map((item, i) => (
          <div key={item.key}>
            <ToggleRow
              label={item.rotulo}
              checked={Boolean(data[item.key])}
              onChange={(val) => onChange(item.key, val)}
              isLast={i === MEDICAMENTOS.length - 1 && !data.usa_aas && !data.usa_varfarina}
            />

            {item.key === "usa_aas" && data.usa_aas && (
              <div style={{ padding: "8px 0 12px 16px", borderBottom: "1px solid var(--border)" }}>
                <Field label="Tipo de prevenção">
                  <ChipGroup
                    options={opcoesPrevencaoAas}
                    value={data.prevencao_aas}
                    onChange={(val) => onChange("prevencao_aas", val)}
                  />
                </Field>
              </div>
            )}

            {item.key === "usa_varfarina" && data.usa_varfarina && (
              <div style={{ padding: "8px 0 12px 16px", display: "flex", flexDirection: "column", gap: 12 }}>
                <Field label="Indicação da varfarina">
                  <ChipGroup
                    options={opcoesIndicacaoVarfarina}
                    value={data.indicacao_varfarina}
                    onChange={(val) => onChange("indicacao_varfarina", val)}
                  />
                </Field>

                {data.indicacao_varfarina === "af" && (
                  <>
                    <Field label="CHADS₂">
                      <Input
                        type="number"
                        placeholder="0–6"
                        min={0}
                        max={6}
                        value={data.chadsvasc_varfarina ?? ""}
                        onChange={(e) => {
                          if (!e.target.value) { onChange("chadsvasc_varfarina", undefined); return; }
                          const v = Math.min(Math.max(Number(e.target.value), 0), 6);
                          onChange("chadsvasc_varfarina", v);
                        }}
                      />
                    </Field>
                    <ToggleRow
                      label="AVC/AIT nos últimos 3 meses"
                      checked={data.avc_3m_varfarina}
                      onChange={(val) => onChange("avc_3m_varfarina", val)}
                      isLast
                    />
                  </>
                )}

                {data.indicacao_varfarina === "vte" && (
                  <>
                    <Field label="Tempo do TEV">
                      <ChipGroup
                        options={opcoesTempoTevVarfarina}
                        value={data.tempo_tev_varfarina}
                        onChange={(val) => onChange("tempo_tev_varfarina", val)}
                      />
                    </Field>
                    <Field label="Trombofilia">
                      <ChipGroup
                        options={opcoesTrombofiliaVarfarina}
                        value={data.trombofilia_varfarina}
                        onChange={(val) => onChange("trombofilia_varfarina", val)}
                      />
                    </Field>
                    <ToggleRow
                      label="Neoplasia ativa"
                      checked={data.neoplasia_ativa_varfarina}
                      onChange={(val) => onChange("neoplasia_ativa_varfarina", val)}
                      isLast
                    />
                  </>
                )}
              </div>
            )}
          </div>
        ))}
      </Card>

      <Card icon={<Activity {...iconProps} />} title="Capacidade Funcional">
        <div style={{ fontSize: 12, color: "var(--ink-mid)", marginBottom: 14, lineHeight: 1.5 }}>
          Deslize para indicar a <strong>atividade máxima</strong> que o paciente consegue realizar.
        </div>

        {/* Rótulos do slider */}
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, fontSize: 10, color: "var(--ink-muted)", fontFamily: "'JetBrains Mono', monospace" }}>
          <span>1 MET</span>
          <span>{SORTED_ACTIVITIES[SORTED_ACTIVITIES.length - 1].mets} METs</span>
        </div>

        <div style={{ position: "relative", padding: "4px 0" }}>
          <input
            type="range"
            min={0}
            max={SORTED_ACTIVITIES.length - 1}
            step={1}
            value={sliderIdx}
            onChange={(e) => {
              const i = Number(e.target.value);
              setSliderIdx(i);
              onChange("mets", SORTED_ACTIVITIES[i].mets);
            }}
            style={{
              width: "100%",
              accentColor: sliderColor,
            }}
          />
        </div>

        {/* Indicador de posição */}
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 2, marginBottom: 10 }}>
          {[0, Math.floor((SORTED_ACTIVITIES.length - 1) / 2), SORTED_ACTIVITIES.length - 1].map((idx) => (
            <div
              key={idx}
              style={{
                width: 2,
                height: 6,
                background: idx === sliderIdx ? sliderColor : "var(--border)",
                borderRadius: 1,
                transition: "background 0.2s",
              }}
            />
          ))}
        </div>

        <div
          style={{
            padding: "12px 14px",
            borderRadius: "var(--r-sm)",
            background: sliderBg,
            border: `1px solid ${sliderBorder}`,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 8,
          }}
        >
          <span style={{ fontSize: 12, color: "var(--ink-mid)", lineHeight: 1.4, flex: 1 }}>
            {currentActivity.rotulo}
          </span>
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 22,
              fontWeight: 600,
              color: sliderColor,
              whiteSpace: "nowrap",
            }}
          >
            {mets} <span style={{ fontSize: 11 }}>METs</span>
          </span>
        </div>

        <div
          style={{
            marginTop: 8,
            fontSize: 12,
            fontWeight: 500,
            color: sliderColor,
            textAlign: "center",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 6,
          }}
        >
          {mets >= 4 ? <CircleCheck size={14} color="var(--green)" /> : <CircleAlert size={14} color="var(--amber)" />}
          {mets >= 4 ? "Capacidade funcional adequada" : "Capacidade funcional reduzida"}
        </div>
      </Card>
    </>
  );
}
