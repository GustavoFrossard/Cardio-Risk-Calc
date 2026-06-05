import * as Print from "expo-print";
import * as Sharing from "expo-sharing";
import { SURGERY_OPTIONS } from "../types";

const SURGERY_RISK_LABELS = {
  low: "Baixo",
  intermediate: "Intermediário",
  high: "Alto",
};

const PDF_TEXT_REPLACEMENTS = new Map([
  ["≥", ">="],
  ["≤", "<="],
  ["–", "-"],
  ["—", "-"],
  ["−", "-"],
  ["₀", "0"],
  ["₁", "1"],
  ["₂", "2"],
  ["₃", "3"],
  ["₄", "4"],
  ["₅", "5"],
  ["₆", "6"],
  ["₇", "7"],
  ["₈", "8"],
  ["₉", "9"],
]);

function getSurgeryTypeLabel(surgeryType) {
  return SURGERY_OPTIONS.find((option) => option.value === surgeryType)?.label || "Não informada";
}

function sanitizePdfText(value) {
  if (value == null) {
    return "";
  }

  let text = String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  for (const [from, to] of PDF_TEXT_REPLACEMENTS.entries()) {
    text = text.split(from).join(to);
  }

  return text;
}

export async function generateReport(result, data) {
  const indexName = sanitizePdfText(result.risk_index === "vsg" ? "VSG-CRI" : "RCRI");
  const surgeryTypeLabel = sanitizePdfText(getSurgeryTypeLabel(data.surgery_type));
  const surgeryRiskLabel = sanitizePdfText(
    SURGERY_RISK_LABELS[result.surgery_risk] || result.surgery_risk || "Não informado",
  );
  const patientName = sanitizePdfText(data.name || "Não informado");
  const patientAge = sanitizePdfText(data.age != null ? `${data.age} anos` : "Não informada");
  const metsLabel = sanitizePdfText(result.mets_label);
  const riskLabel = sanitizePdfText(result.risk_label);

  const dateStr = new Date().toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  const riskColorHex =
    result.risk_class === "low"
      ? "#16a34a"
      : result.risk_class === "intermediate"
      ? "#ca8a04"
      : "#dc2626";

  const activeConditionsHtml = result.has_active_conditions
    ? `<div class="active-conditions">
        <p class="active-label">[!] CONDIÇÕES CARDÍACAS ATIVAS DETECTADAS</p>
        ${result.active_conditions.map((c) => `<p class="active-item">- ${sanitizePdfText(c)}</p>`).join("")}
      </div>`
    : "";

  const riskFactorsHtml =
    result.risk_factors.length > 0
      ? `<div class="section">
          <p class="section-title">Fatores de Risco Identificados</p>
          ${result.risk_factors.map((f) => `<p class="bullet">- ${sanitizePdfText(f)}</p>`).join("")}
        </div>`
      : "";

  const medicationHtml =
    result.medication_advice.length > 0
      ? `<div class="section">
          <p class="section-title">Manejo de Medicamentos</p>
          ${result.medication_advice
            .map(
              (med) =>
                `<div class="med-item">
                  <p class="med-title">${sanitizePdfText(med.medication)} - ${sanitizePdfText(med.action)}</p>
                  <p class="med-detail">${sanitizePdfText(med.detail)}</p>
                </div>`,
            )
            .join("")}
        </div>`
      : "";

  const examsHtml =
    result.recommended_exams.length > 0
      ? `<div class="section">
          <p class="section-title">Exames Recomendados</p>
          ${result.recommended_exams.map((e) => `<p class="bullet">- ${sanitizePdfText(e)}</p>`).join("")}
        </div>`
      : "";

  const recommendationsHtml =
    result.recommendations.length > 0
      ? `<div class="section">
          <p class="section-title">Recomendações</p>
          ${result.recommendations
            .map(
              (rec) =>
                `<div class="med-item">
                  <p class="med-title">${sanitizePdfText(rec.title)}</p>
                  <p class="med-detail">${sanitizePdfText(rec.body)}</p>
                </div>`,
            )
            .join("")}
        </div>`
      : "";

  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    body { font-family: Helvetica, Arial, sans-serif; color: #1e1e1e; font-size: 10pt; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .header { background-color: #0f4c81 !important; color: white; padding: 12mm 20mm 10mm; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .header h1 { font-size: 13pt; font-weight: bold; margin-bottom: 3mm; color: white; }
    .header p { font-size: 8pt; opacity: 0.85; color: white; }
    .body { padding: 10mm 20mm; }
    .section { margin-bottom: 10mm; }
    .divider { border: none; border-top: 0.3mm solid #c8c8c8; margin: 6mm 0; }
    .section-title { font-size: 10pt; font-weight: bold; margin-bottom: 4mm; }
    p.line { font-size: 9pt; margin-bottom: 2mm; }
    p.bullet { font-size: 9pt; margin-bottom: 2mm; padding-left: 4mm; }
    .risk-box { border-radius: 2mm; padding: 4mm 5mm; margin-bottom: 6mm; display: table; width: 100%; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .risk-box-label { font-size: 13pt; font-weight: bold; color: white !important; display: table-cell; }
    .risk-box-score { font-size: 8pt; color: white !important; display: table-cell; text-align: right; vertical-align: middle; }
    .active-conditions { background-color: #fee2e2 !important; border: 0.3mm solid #f5b0aa; border-radius: 2mm; padding: 4mm 5mm; margin-bottom: 8mm; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .active-label { color: #b91c1c !important; font-weight: bold; font-size: 9pt; margin-bottom: 3mm; }
    .active-item { font-size: 9pt; margin-bottom: 1.5mm; padding-left: 4mm; color: #7f1d1d !important; }
    .med-item { margin-bottom: 5mm; border-left: 0.8mm solid #888; padding-left: 4mm; }
    .med-title { font-size: 9pt; font-weight: bold; margin-bottom: 1.5mm; }
    .med-detail { font-size: 9pt; line-height: 1.5; }
    .footer { margin-top: 12mm; padding-top: 4mm; border-top: 0.3mm solid #eee; text-align: center; font-size: 7pt; color: #aaa; line-height: 1.6; }
  </style>
</head>
<body>
  <div class="header">
    <h1>Avaliação de Risco Cardiovascular Perioperatório</h1>
    <p>Relatório gerado em ${dateStr}</p>
  </div>
  <div class="body">

    <div class="section">
      <p class="section-title">Dados do Paciente</p>
      <p class="line">Paciente: ${patientName}</p>
      <p class="line">Idade: ${patientAge}</p>
      <p class="line">Cirurgia: ${surgeryTypeLabel}</p>
      <p class="line">Risco cirúrgico: ${surgeryRiskLabel}</p>
      <p class="line">Capacidade Funcional: ${result.mets} METs - ${metsLabel}</p>
    </div>

    <hr class="divider">

    ${activeConditionsHtml}

    <div class="section">
      <p class="section-title">Resultado - Índice ${indexName}</p>
      <div class="risk-box" style="background:${riskColorHex}">
        <span class="risk-box-label">${riskLabel}</span>
        <span class="risk-box-score">Score: ${result.score} pt${result.score !== 1 ? "s" : ""}</span>
      </div>
    </div>

    ${riskFactorsHtml}
    ${medicationHtml}
    ${examsHtml}
    ${recommendationsHtml}

    <div class="footer">
      Ferramenta de suporte clínico. Não substitui o julgamento médico individualizado.<br>
      Baseado na Diretriz Brasileira de Avaliação Cardiovascular Perioperatória, RCRI (Lee) e VSG.
    </div>
  </div>
</body>
</html>`;

  try {
    const { uri } = await Print.printToFileAsync({ html });
    if (await Sharing.isAvailableAsync()) {
      await Sharing.shareAsync(uri, {
        mimeType: "application/pdf",
        dialogTitle: "CardioRisk - Relatório",
        UTI: "com.adobe.pdf",
      });
    }
  } catch (err) {
    console.error("Erro ao gerar relatório:", err);
  }
}
