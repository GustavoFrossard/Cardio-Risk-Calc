import { useState } from "react";
import { View, Text } from "react-native";
import Slider from "@react-native-community/slider";
import { Card, Field, Input, ToggleRow, ChipGroup } from "../ui";
import { FUNCTIONAL_QUESTIONS } from "../../types";
import { theme } from "../../theme";

const SORTED_ACTIVITIES = [
  { label: "Nenhuma atividade / acamado", mets: 1 },
  ...FUNCTIONAL_QUESTIONS.slice().sort((a, b) => a.mets - b.mets),
];

const COMORBIDITIES = [
  { key: "obesity", label: "Obesidade", description: "IMC ≥ 30" },
  { key: "known_hf", label: "IC conhecida ou suspeita", description: "Insuficiência cardíaca" },
  { key: "known_valvular_disease", label: "Doença valvar conhecida ou suspeita" },
  { key: "known_cad", label: "Doença coronariana conhecida ou suspeita" },
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

export function EtapaDadosPaciente({ data, onChange }) {
  const [sliderIdx, setSliderIdx] = useState(() => {
    let best = 0;
    let minDiff = Infinity;
    for (let i = SORTED_ACTIVITIES.length - 1; i >= 0; i--) {
      const diff = Math.abs(SORTED_ACTIVITIES[i].mets - data.mets);
      if (diff < minDiff) {
        minDiff = diff;
        best = i;
      }
    }
    return best;
  });

  const currentActivity = SORTED_ACTIVITIES[sliderIdx];
  const mets = currentActivity.mets;

  return (
    <>
      <Card icon="👤" title="Identificação">
        <Field label="Nome / Identificador" style={{ marginBottom: 12 }}>
          <Input
            placeholder="Opcional"
            value={data.name ?? ""}
            onChange={(text) => onChange("name", text)}
          />
        </Field>
        <Field label="Idade">
          <Input
            placeholder="—"
            unit="anos"
            keyboardType="numeric"
            value={data.age != null ? String(data.age) : ""}
            onChange={(text) => {
              if (!text) {
                onChange("age", undefined);
                return;
              }
              const v = Math.min(Math.max(Number(text), 0), 120);
              onChange("age", isNaN(v) ? undefined : v);
            }}
          />
        </Field>
      </Card>

      <Card icon="🩺" title="Comorbidades">
        {COMORBIDITIES.map((item, i) => (
          <ToggleRow
            key={item.key}
            label={item.label}
            description={item.description}
            checked={Boolean(data[item.key])}
            onChange={(val) => onChange(item.key, val)}
            isLast={
              i === COMORBIDITIES.length - 1 &&
              !data.known_hf &&
              !data.known_valvular_disease
            }
          />
        ))}

        {(data.known_hf || data.known_valvular_disease) ? (
          <View
            style={{
              paddingVertical: 8,
              paddingLeft: 16,
              gap: 12,
              borderTopWidth: 1,
              borderTopColor: theme.border,
            }}
          >
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
          </View>
        ) : null}
      </Card>

      <Card icon="💊" title="Medicamentos em Uso">
        {MEDICATIONS.map((item, i) => (
          <View key={item.key}>
            <ToggleRow
              label={item.label}
              checked={Boolean(data[item.key])}
              onChange={(val) => onChange(item.key, val)}
              isLast={i === MEDICATIONS.length - 1 && !data.uses_aas && !data.uses_warfarin}
            />

            {item.key === "uses_aas" && data.uses_aas ? (
              <View
                style={{
                  paddingTop: 8,
                  paddingBottom: 12,
                  paddingLeft: 16,
                  borderBottomWidth: 1,
                  borderBottomColor: theme.border,
                }}
              >
                <Field label="Tipo de prevenção">
                  <ChipGroup
                    options={aasPreventionOptions}
                    value={data.aas_prevention}
                    onChange={(val) => onChange("aas_prevention", val)}
                  />
                </Field>
              </View>
            ) : null}

            {item.key === "uses_warfarin" && data.uses_warfarin ? (
              <View style={{ paddingTop: 8, paddingBottom: 12, paddingLeft: 16, gap: 12 }}>
                <Field label="Indicação da varfarina">
                  <ChipGroup
                    options={warfarinIndicationOptions}
                    value={data.warfarin_indication}
                    onChange={(val) => onChange("warfarin_indication", val)}
                  />
                </Field>

                {data.warfarin_indication === "af" ? (
                  <>
                    <Field label="CHADS₂">
                      <Input
                        placeholder="0–6"
                        keyboardType="numeric"
                        value={data.warfarin_chadsvasc != null ? String(data.warfarin_chadsvasc) : ""}
                        onChange={(text) => {
                          if (!text) {
                            onChange("warfarin_chadsvasc", undefined);
                            return;
                          }
                          const v = Math.min(Math.max(Number(text), 0), 6);
                          onChange("warfarin_chadsvasc", isNaN(v) ? undefined : v);
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
                ) : null}

                {data.warfarin_indication === "vte" ? (
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
                ) : null}
              </View>
            ) : null}
          </View>
        ))}
      </Card>

      <Card icon="📊" title="Capacidade Funcional">
        <Text style={{ fontSize: 12, color: theme.inkMid, marginBottom: 12, lineHeight: 18 }}>
          Deslize para indicar a{" "}
          <Text style={{ fontWeight: "bold" }}>atividade máxima</Text>
          {" "}que o paciente consegue realizar.
        </Text>

        <Slider
          style={{ width: "100%", height: 40 }}
          minimumValue={0}
          maximumValue={SORTED_ACTIVITIES.length - 1}
          step={1}
          value={sliderIdx}
          onValueChange={(i) => {
            const idx = Math.round(i);
            setSliderIdx(idx);
            onChange("mets", SORTED_ACTIVITIES[idx].mets);
          }}
          minimumTrackTintColor={mets >= 4 ? theme.green : theme.amber}
          maximumTrackTintColor={theme.border}
          thumbTintColor={mets >= 4 ? theme.green : theme.amber}
        />

        <View
          style={{
            marginTop: 10,
            padding: 12,
            borderRadius: theme.rSm,
            backgroundColor: mets >= 4 ? theme.greenSoft : theme.amberSoft,
            borderWidth: 1,
            borderColor: mets >= 4 ? "#A7D4BB" : "#FCD34D",
            flexDirection: "row",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 8,
          }}
        >
          <Text style={{ fontSize: 12, color: theme.inkMid, lineHeight: 17, flex: 1 }}>
            {currentActivity.label}
          </Text>
          <Text
            style={{
              fontFamily: "monospace",
              fontSize: 20,
              fontWeight: "600",
              color: mets >= 4 ? theme.green : theme.amber,
            }}
          >
            {mets}{" "}
            <Text style={{ fontSize: 11 }}>METs</Text>
          </Text>
        </View>

        <Text
          style={{
            marginTop: 6,
            fontSize: 12,
            fontWeight: "500",
            color: theme.inkMid,
            textAlign: "center",
          }}
        >
          {mets >= 4 ? "✅ Capacidade funcional adequada" : "⚠️ Capacidade funcional reduzida"}
        </Text>
      </Card>
    </>
  );
}
