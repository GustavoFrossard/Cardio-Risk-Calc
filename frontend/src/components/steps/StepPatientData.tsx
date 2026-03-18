import { useState } from "react";
import { Card, Field, Input, ToggleRow, ChipGroup } from "../ui";
import type { PatientData } from "../../types";
import { FUNCTIONAL_QUESTIONS } from "../../types";

const SORTED_ACTIVITIES = [
  { label: "Nenhuma atividade / acamado", mets: 1 },
  ...FUNCTIONAL_QUESTIONS.slice().sort((a, b) => a.mets - b.mets),
];

interface Props {
  data: PatientData;
  onChange: <K extends keyof PatientData>(key: K, value: PatientData[K]) => void;
}

const COMORBIDITIES: Array<{ key: keyof PatientData; label: string; description?: string }> = [
  { key: "obesity", label: "Obesidade", description: "IMC ≥ 30" },
  { key: "known_hf", label: "IC conhecida ou suspeita", description: "Insuficiência cardíaca" },
  { key: "known_valvular_disease", label: "Doença valvar conhecida ou suspeita" },
  { key: "known_cad", label: "Doença coronariana conhecida ou suspeita" },
];

const MEDICATIONS: Array<{ key: keyof PatientData; label: string }> = [
  { key: "uses_aas", label: "AAS (Ácido Acetilsalicílico)" },
  { key: "uses_clopidogrel", label: "Clopidogrel" },
  { key: "uses_ticagrelor", label: "Ticagrelor" },
  { key: "uses_prasugrel", label: "Prasugrel" },
  { key: "uses_warfarin", label: "Varfarina" },
];

const aasPreventionOptions = [
  { value: "primary" as const, label: "Primária" },
  { value: "secondary" as const, label: "Secundária" },
];

const warfarinIndicationOptions = [
  { value: "af" as const, label: "FA" },
  { value: "vte" as const, label: "TEV" },
  { value: "mechanical_valve" as const, label: "Prótese Mecânica" },
  { value: "rheumatic" as const, label: "Valvar Reumática" },
];

const warfarinVteTimingOptions = [
  { value: "recent" as const, label: "< 3 meses" },
  { value: "3_12m" as const, label: "3–12 meses" },
  { value: "over_12m" as const, label: "> 12 meses" },
];

const warfarinThrombophiliaOptions = [
  { value: "severe" as const, label: "Grave" },
  { value: "mild" as const, label: "Leve" },
  { value: "none" as const, label: "Não" },
];

export function StepPatientData({ data, onChange }: Props) {
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

  return (
    <>
      {/* Identification */}
      <Card icon="👤" title="Identificação">
        <Field label="Nome / Identificador" style={{ marginBottom: 12 }}>
          <Input
            type="text"
            placeholder="Opcional"
            value={data.name ?? ""}
            onChange={(e) => onChange("name", e.target.value)}
          />
        </Field>
        <Field label="Idade">
          <Input
            type="number"
            placeholder="—"
            unit="anos"
            value={data.age ?? ""}
            min={0}
            max={120}
            onChange={(e) => {
              if (!e.target.value) { onChange("age", undefined); return; }
              const v = Math.min(Math.max(Number(e.target.value), 0), 120);
              onChange("age", v);
            }}
          />
        </Field>
      </Card>

      {/* Comorbidities */}
      <Card icon="🩺" title="Comorbidades">
        {COMORBIDITIES.map((item, i) => (
          <ToggleRow
            key={item.key}
            label={item.label}
            description={item.description}
            checked={Boolean(data[item.key])}
            onChange={(val) => onChange(item.key, val as PatientData[typeof item.key])}
            isLast={i === COMORBIDITIES.length - 1}
          />
        ))}
      </Card>

      {/* Medications */}
      <Card icon="💊" title="Medicamentos em Uso">
        {MEDICATIONS.map((item, i) => (
          <div key={item.key}>
            <ToggleRow
              label={item.label}
              checked={Boolean(data[item.key])}
              onChange={(val) => onChange(item.key, val as PatientData[typeof item.key])}
              isLast={i === MEDICATIONS.length - 1 && !data.uses_aas && !data.uses_warfarin}
            />

            {/* AAS sub-question: prevention type */}
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

            {/* Warfarin sub-questions */}
            {item.key === "uses_warfarin" && data.uses_warfarin && (
              <div style={{ padding: "8px 0 12px 16px", display: "flex", flexDirection: "column", gap: 12 }}>
                <Field label="Indicação da varfarina">
                  <ChipGroup
                    options={warfarinIndicationOptions}
                    value={data.warfarin_indication}
                    onChange={(val) => onChange("warfarin_indication", val)}
                  />
                </Field>

                {/* FA sub-questions */}
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

                {/* VTE sub-questions */}
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

      {/* Functional Capacity */}
      <Card icon="📊" title="Capacidade Funcional">
        <div style={{ fontSize: 12, color: "var(--ink-mid)", marginBottom: 12, lineHeight: 1.5 }}>
          Deslize para indicar a <strong>atividade máxima</strong> que o paciente consegue realizar.
        </div>

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
          style={{ width: "100%", accentColor: mets >= 4 ? "var(--green)" : "var(--amber)" }}
        />

        {/* Selected activity */}
        <div
          style={{
            marginTop: 10,
            padding: "10px 14px",
            borderRadius: "var(--r-sm)",
            background: mets >= 4 ? "var(--green-soft)" : "var(--amber-soft)",
            border: `1px solid ${mets >= 4 ? "#A7D4BB" : "#FCD34D"}`,
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
              fontSize: 20,
              fontWeight: 600,
              color: mets >= 4 ? "var(--green)" : "var(--amber)",
              whiteSpace: "nowrap",
            }}
          >
            {mets} <span style={{ fontSize: 11 }}>METs</span>
          </span>
        </div>

        <div style={{ marginTop: 6, fontSize: 12, fontWeight: 500, color: "var(--ink-mid)", textAlign: "center" }}>
          {mets >= 4 ? "✅ Capacidade funcional adequada" : "⚠️ Capacidade funcional reduzida"}
        </div>
      </Card>
    </>
  );
}
