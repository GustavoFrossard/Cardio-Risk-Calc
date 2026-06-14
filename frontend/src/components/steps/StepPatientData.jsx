import { useEffect, useState } from "react";
import { Activity, BrainCircuit, CircleAlert, CircleCheck, Pill, Stethoscope, UserRound } from "lucide-react";
import { Card, Field, Input, AgeInput, ToggleRow, ChipGroup } from "../ui";
import { FUNCTIONAL_QUESTIONS } from "../../types";

const SORTED_ACTIVITIES = [
  { label: "Nenhuma atividade / acamado", mets: 1 },
  ...FUNCTIONAL_QUESTIONS.slice().sort((a, b) => a.mets - b.mets),
];

const COMORBIDITIES = [
  { key: "obesity", label: "Obesidade", description: "IMC ≥ 30" },
  { key: "known_hf", label: "IC conhecida ou suspeita", description: "Insuficiência cardíaca" },
  { key: "known_valvular_disease", label: "Doença valvar conhecida ou suspeita", description: "Valvopatia diagnosticada ou suspeita clinicamente" },
  { key: "known_cad", label: "Doença coronariana conhecida ou suspeita", description: "Angina, IAM prévio, stent ou cirurgia de revascularização" },
];

const MEDICATIONS = [
  { key: "uses_aas", label: "AAS (Ácido Acetilsalicílico)" },
  { key: "uses_clopidogrel", label: "Clopidogrel" },
  { key: "uses_ticagrelor", label: "Ticagrelor" },
  { key: "uses_prasugrel", label: "Prasugrel" },
  { key: "uses_warfarin", label: "Varfarina" },
];

const aasPreventionOptions = [
  { value: "primary", label: "Primária" },
  { value: "secondary", label: "Secundária" },
];

const warfarinIndicationOptions = [
  { value: "af", label: "FA" },
  { value: "vte", label: "TEV" },
  { value: "mechanical_valve", label: "Prótese Mecânica" },
  { value: "rheumatic", label: "Valvar Reumática" },
];

const warfarinVteTimingOptions = [
  { value: "recent", label: "< 3 meses" },
  { value: "3_12m", label: "3–12 meses" },
  { value: "over_12m", label: "> 12 meses" },
];

const warfarinThrombophiliaOptions = [
  { value: "severe", label: "Grave" },
  { value: "mild", label: "Leve" },
  { value: "none", label: "Não" },
];

export function EtapaDadosPaciente({ data, onChange, onAnalyzeClinicalText, isAnalyzing, nlpResult }) {
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

  const iconProps = { size: 16, strokeWidth: 2.2 };

  const handleAnalyze = async () => {
    const text = clinicalText.trim();
    if (!text || !onAnalyzeClinicalText) return;
    await onAnalyzeClinicalText(text);
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
  const sliderBorder = mets >= 4 ? "#A7D4BB" : "#FCD34D";

  return (
    <>
      <Card icon={<BrainCircuit {...iconProps} />} title="Pré-preenchimento por texto clínico">
        <Field label="Cole aqui o caso clínico">
          <textarea
            placeholder="Ex: Paciente de 67 anos com HAS e DM2 em insulinoterapia, antecedente de AVC, em programação de colecistectomia laparoscópica..."
            value={clinicalText}
            onChange={(e) => setClinicalText(e.target.value)}
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
          disabled={isAnalyzing || !clinicalText.trim()}
          style={{
            marginTop: 12,
            border: "none",
            borderRadius: "var(--r-sm)",
            background: isAnalyzing ? "#91A4CC" : "var(--blue)",
            color: "white",
            fontSize: 13,
            fontWeight: 600,
            padding: "10px 14px",
            cursor: isAnalyzing ? "not-allowed" : "pointer",
            width: "100%",
          }}
        >
          {isAnalyzing ? "Analisando caso clínico..." : "Analisar e auto-preencher"}
        </button>

        {nlpResult && (
          <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
            <div
              style={{
                borderRadius: "var(--r-sm)",
                background: "var(--blue-soft)",
                border: "1px solid #BDD3FB",
                padding: "10px 12px",
                fontSize: 12,
                color: "#1A3B7A",
                lineHeight: 1.45,
              }}
            >
              <strong>{nlpResult?.summary?.autofill_count ?? 0}</strong> campos auto-preenchidos. Modelo:{" "}
              <strong>{nlpResult?.model?.name}</strong> ({nlpResult?.model?.status}).
            </div>

            {Array.isArray(nlpResult?.missing_critical) && nlpResult.missing_critical.length > 0 && (
              <div
                style={{
                  borderRadius: "var(--r-sm)",
                  background: "var(--amber-soft)",
                  border: "1px solid #FCD34D",
                  padding: "10px 12px",
                  fontSize: 12,
                  color: "#7A5000",
                  lineHeight: 1.5,
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Informações críticas ausentes</div>
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {nlpResult.missing_critical.map((item) => (
                    <li key={item.field}>{item.label}: {item.question}</li>
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
            value={data.name ?? ""}
            onChange={(e) => onChange("name", e.target.value)}
          />
        </Field>
        <Field label="Idade">
          <AgeInput
            value={data.age}
            onChange={(v) => onChange("age", v)}
          />
        </Field>
      </Card>

      <Card icon={<Stethoscope {...iconProps} />} title="Comorbidades">
        {COMORBIDITIES.map((item, i) => (
          <ToggleRow
            key={item.key}
            label={item.label}
            description={item.description}
            checked={Boolean(data[item.key])}
            onChange={(val) => onChange(item.key, val)}
            isLast={i === COMORBIDITIES.length - 1 && !data.known_hf && !data.known_valvular_disease}
          />
        ))}

        {(data.known_hf || data.known_valvular_disease) && (
          <div style={{ padding: "8px 0 12px 16px", display: "flex", flexDirection: "column", gap: 12, borderTop: "1px solid var(--border)" }}>
            <ToggleRow
              label="Ecocardiograma recente (< 6 meses)"
              checked={Boolean(data.recent_echo)}
              onChange={(val) => onChange("recent_echo", val)}
              isLast={false}
            />
            <ToggleRow
              label="Piora dos sintomas"
              checked={Boolean(data.worsening_symptoms)}
              onChange={(val) => onChange("worsening_symptoms", val)}
              isLast={true}
            />
          </div>
        )}
      </Card>

      <Card icon={<Pill {...iconProps} />} title="Medicamentos em Uso">
        {MEDICATIONS.map((item, i) => (
          <div key={item.key}>
            <ToggleRow
              label={item.label}
              checked={Boolean(data[item.key])}
              onChange={(val) => onChange(item.key, val)}
              isLast={i === MEDICATIONS.length - 1 && !data.uses_aas && !data.uses_warfarin}
            />

            {item.key === "uses_aas" && data.uses_aas && (
              <div style={{ padding: "8px 0 12px 16px", borderBottom: "1px solid var(--border)" }}>
                <Field label="Tipo de prevenção">
                  <ChipGroup
                    options={aasPreventionOptions}
                    value={data.aas_prevention}
                    onChange={(val) => onChange("aas_prevention", val)}
                  />
                </Field>
              </div>
            )}

            {item.key === "uses_warfarin" && data.uses_warfarin && (
              <div style={{ padding: "8px 0 12px 16px", display: "flex", flexDirection: "column", gap: 12 }}>
                <Field label="Indicação da varfarina">
                  <ChipGroup
                    options={warfarinIndicationOptions}
                    value={data.warfarin_indication}
                    onChange={(val) => onChange("warfarin_indication", val)}
                  />
                </Field>

                {data.warfarin_indication === "af" && (
                  <>
                    <Field label="CHADS₂">
                      <Input
                        type="number"
                        placeholder="0–6"
                        min={0}
                        max={6}
                        value={data.warfarin_chadsvasc ?? ""}
                        onChange={(e) => {
                          if (!e.target.value) { onChange("warfarin_chadsvasc", undefined); return; }
                          const v = Math.min(Math.max(Number(e.target.value), 0), 6);
                          onChange("warfarin_chadsvasc", v);
                        }}
                      />
                    </Field>
                    <ToggleRow
                      label="AVC/AIT nos últimos 3 meses"
                      checked={data.warfarin_stroke_3m}
                      onChange={(val) => onChange("warfarin_stroke_3m", val)}
                      isLast
                    />
                  </>
                )}

                {data.warfarin_indication === "vte" && (
                  <>
                    <Field label="Tempo do TEV">
                      <ChipGroup
                        options={warfarinVteTimingOptions}
                        value={data.warfarin_vte_timing}
                        onChange={(val) => onChange("warfarin_vte_timing", val)}
                      />
                    </Field>
                    <Field label="Trombofilia">
                      <ChipGroup
                        options={warfarinThrombophiliaOptions}
                        value={data.warfarin_thrombophilia}
                        onChange={(val) => onChange("warfarin_thrombophilia", val)}
                      />
                    </Field>
                    <ToggleRow
                      label="Neoplasia ativa"
                      checked={data.warfarin_active_neoplasia}
                      onChange={(val) => onChange("warfarin_active_neoplasia", val)}
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

        {/* Slider labels */}
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

        {/* Position indicator */}
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
            {currentActivity.label}
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
