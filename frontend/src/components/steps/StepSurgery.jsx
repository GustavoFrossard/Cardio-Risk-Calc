import { AlertTriangle, Hospital, Siren } from "lucide-react";
import { Card, ToggleRow, InfoBox, SearchSelect } from "../ui";
import { OPCOES_CIRURGIA } from "../../types";

const GRUPOS_RISCO = [
  { rotulo: "Baixo Risco (< 1%)", risco: "baixo" },
  { rotulo: "Risco Intermediário (1–5%)", risco: "intermediario" },
  { rotulo: "Alto Risco (> 5%)", risco: "alto" },
];

const OPCOES_CIRURGIA_PLANA = GRUPOS_RISCO.flatMap((grupo) => [
  { valor: `__header_${grupo.risco}`, rotulo: grupo.rotulo, ehCabecalho: true },
  ...OPCOES_CIRURGIA.filter((o) => o.risco === grupo.risco).map((o) => ({
    valor: o.valor,
    rotulo: o.rotulo,
  })),
]);

const CV_CONDICOES = [
  {
    key: "cv_coronaria_aguda",
    rotulo: "Síndrome coronariana aguda",
    descricao: "IAM agudo (< 30 dias) ou angina instável",
  },
  {
    key: "cv_aorta_instavel",
    rotulo: "Doenças instáveis da aorta torácica",
    descricao: "Dissecção aguda, aneurisma sintomático",
  },
  {
    key: "cv_edema_pulmonar_agudo",
    rotulo: "Edema agudo dos pulmões",
    descricao: "Episódio atual ou recente",
  },
  {
    key: "cv_choque_cardiogenico",
    rotulo: "Choque cardiogênico",
    descricao: "Hipoperfusão por causa cardíaca",
  },
  {
    key: "cv_ic_nyha_3_4",
    rotulo: "IC classe funcional III/IV (NYHA)",
    descricao: "Dispneia aos pequenos esforços ou em repouso",
  },
  {
    key: "cv_angina_ccs_3_4",
    rotulo: "Angina classe funcional CCS III/IV",
    descricao: "Angina em atividades leves ou em repouso",
  },
  {
    key: "cv_arritmia_grave",
    rotulo: "Bradiarritmias ou taquiarritmias graves",
    descricao: "BAVT, TV sustentada, arritmias sintomáticas",
  },
  {
    key: "cv_has_nao_controlada",
    rotulo: "HAS não controlada",
    descricao: "PA > 180 × 110 mmHg",
  },
  {
    key: "cv_fa_alta_resposta",
    rotulo: "FA de alta resposta ventricular",
    descricao: "FC > 120 bpm",
  },
  {
    key: "cv_hap_sintomatica",
    rotulo: "HAP sintomática",
    descricao: "Hipertensão arterial pulmonar com sintomas",
  },
  {
    key: "cv_valvopatia_grave",
    rotulo: "Estenose aórtica/mitral importante sintomática",
    descricao: "Estenose valvar grave com repercussão hemodinâmica",
  },
];

export function EtapaCirurgia({ data, onChange }) {
  const iconProps = { size: 16, strokeWidth: 2.2 };

  const handleSurgeryChange = (valor) => {
    const opcao = OPCOES_CIRURGIA.find((o) => o.valor === valor);
    onChange("tipo_cirurgia", valor);
    onChange("risco_cirurgia", opcao?.risco ?? "");
    onChange("eh_vascular", opcao?.vascular ?? false);
  };

  const opcaoSelecionada = OPCOES_CIRURGIA.find((o) => o.valor === data.tipo_cirurgia);
  const badgeRisco = opcaoSelecionada
    ? { baixo: "Baixo", intermediario: "Intermediário", alto: "Alto" }[opcaoSelecionada.risco]
    : null;

  return (
    <>
      <Card icon={<Hospital {...iconProps} />} title="Identificação da Cirurgia">
        <SearchSelect
          value={data.tipo_cirurgia}
          onChange={handleSurgeryChange}
          options={OPCOES_CIRURGIA_PLANA}
          placeholder="Selecione o procedimento..."
        />

        {opcaoSelecionada && (
          <div
            style={{
              marginTop: 12,
              display: "flex",
              gap: 8,
              flexWrap: "wrap",
            }}
          >
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                padding: "4px 10px",
                borderRadius: 999,
                background:
                  opcaoSelecionada.risco === "baixo"
                    ? "var(--green-soft)"
                    : opcaoSelecionada.risco === "intermediario"
                    ? "var(--amber-soft)"
                    : "var(--red-soft)",
                color:
                  opcaoSelecionada.risco === "baixo"
                    ? "var(--green)"
                    : opcaoSelecionada.risco === "intermediario"
                    ? "var(--amber)"
                    : "var(--red)",
              }}
            >
              Risco {badgeRisco}
            </span>
            {opcaoSelecionada.vascular && (
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  padding: "4px 10px",
                  borderRadius: 999,
                  background: "var(--blue-soft)",
                  color: "var(--blue)",
                }}
              >
                Cirurgia Vascular → VSG
              </span>
            )}
          </div>
        )}
      </Card>

      <Card icon={<Siren {...iconProps} />} title="Condições Cardiovasculares Ativas">
        <InfoBox icon={<AlertTriangle size={16} strokeWidth={2.2} color="#1A3B7A" />}>
          Condições que requerem avaliação e tratamento <strong>antes</strong> do procedimento cirúrgico.
        </InfoBox>
        <div style={{ marginTop: 10 }}>
          {CV_CONDICOES.map((item, i) => (
            <ToggleRow
              key={item.key}
              label={item.rotulo}
              description={item.descricao}
              checked={Boolean(data[item.key])}
              onChange={(val) => onChange(item.key, val)}
              isLast={i === CV_CONDICOES.length - 1}
            />
          ))}
        </div>
      </Card>
    </>
  );
}
