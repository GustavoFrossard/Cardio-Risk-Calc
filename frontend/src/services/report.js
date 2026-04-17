import jsPDF from "jspdf";

const MARGIN = 20;
const PAGE_W = 210;
const CONTENT_W = PAGE_W - MARGIN * 2;

function addPage(doc, y, needed) {
  if (y + needed > 280) {
    doc.addPage();
    return MARGIN;
  }
  return y;
}

export function generateReport(result, data) {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const indexName = result.risk_index === "vsg" ? "VSG-CRI" : "RCRI";
  let y = MARGIN;

  // ─── Header ──────────────────────────────────────────────────────
  doc.setFillColor(15, 76, 129);
  doc.rect(0, 0, PAGE_W, 36, "F");

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(16);
  doc.setFont("helvetica", "bold");
  doc.text("Avaliação de Risco Cardiovascular Perioperatório", MARGIN, 16);

  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  const dateStr = new Date().toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
  doc.text(`Relatório gerado em ${dateStr}`, MARGIN, 26);

  y = 46;
  doc.setTextColor(30, 30, 30);

  // ─── Patient info ───────────────────────────────────────────────
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text("Dados do Paciente", MARGIN, y);
  y += 7;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  const patientName = data.name || "Não informado";
  const patientAge = data.age != null ? `${data.age} anos` : "Não informada";
  doc.text(`Paciente: ${patientName}`, MARGIN, y);
  y += 5;
  doc.text(`Idade: ${patientAge}`, MARGIN, y);
  y += 5;
  doc.text(`Cirurgia: ${result.surgery_label}`, MARGIN, y);
  y += 5;
  doc.text(`Risco cirúrgico: ${result.surgery_risk}`, MARGIN, y);
  y += 5;
  doc.text(`Capacidade funcional: ${result.mets} METs — ${result.mets_label}`, MARGIN, y);
  y += 10;

  doc.setDrawColor(200, 200, 200);
  doc.line(MARGIN, y, MARGIN + CONTENT_W, y);
  y += 8;

  if (result.has_active_conditions) {
    y = addPage(doc, y, 20 + result.active_conditions.length * 5);
    doc.setFillColor(254, 226, 226);
    const boxH = 12 + result.active_conditions.length * 5;
    doc.roundedRect(MARGIN, y - 3, CONTENT_W, boxH, 2, 2, "F");

    doc.setFont("helvetica", "bold");
    doc.setFontSize(10);
    doc.setTextColor(185, 28, 28);
    doc.text("⚠ CONDIÇÕES CARDÍACAS ATIVAS DETECTADAS", MARGIN + 4, y + 3);
    y += 8;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    for (const cond of result.active_conditions) {
      doc.text(`• ${cond}`, MARGIN + 6, y);
      y += 5;
    }
    y += 6;
    doc.setTextColor(30, 30, 30);
  }

  y = addPage(doc, y, 30);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.text(`Resultado — Índice ${indexName}`, MARGIN, y);
  y += 8;

  const riskColor =
    result.risk_class === "low" ? [22, 163, 74] :
    result.risk_class === "intermediate" ? [202, 138, 4] :
    [220, 38, 38];

  doc.setFillColor(riskColor[0], riskColor[1], riskColor[2]);
  doc.roundedRect(MARGIN, y - 3, CONTENT_W, 18, 2, 2, "F");

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text(`${result.mace_risk_pct.toFixed(1)}%  —  ${result.risk_label}`, MARGIN + 6, y + 7);
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.text(`Score: ${result.score} pt${result.score !== 1 ? "s" : ""}  |  Classe ${result.score_class}`, MARGIN + CONTENT_W - 4, y + 7, { align: "right" });

  y += 22;
  doc.setTextColor(30, 30, 30);

  if (result.risk_factors.length > 0) {
    y = addPage(doc, y, 10 + result.risk_factors.length * 5);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Fatores de Risco Identificados", MARGIN, y);
    y += 6;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    for (const factor of result.risk_factors) {
      y = addPage(doc, y, 6);
      doc.text(`• ${factor}`, MARGIN + 4, y);
      y += 5;
    }
    y += 4;
  }

  if (result.medication_advice.length > 0) {
    y = addPage(doc, y, 14);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Manejo de Medicamentos", MARGIN, y);
    y += 7;

    doc.setFontSize(9);
    for (const med of result.medication_advice) {
      y = addPage(doc, y, 14);
      doc.setFont("helvetica", "bold");
      doc.text(`${med.medication} — ${med.action}`, MARGIN + 4, y);
      y += 4;
      doc.setFont("helvetica", "normal");
      const lines = doc.splitTextToSize(med.detail, CONTENT_W - 8);
      doc.text(lines, MARGIN + 4, y);
      y += lines.length * 4 + 4;
    }
    y += 2;
  }

  if (result.recommended_exams.length > 0) {
    y = addPage(doc, y, 10 + result.recommended_exams.length * 5);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Exames Recomendados", MARGIN, y);
    y += 6;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    for (const exam of result.recommended_exams) {
      y = addPage(doc, y, 6);
      doc.text(`• ${exam}`, MARGIN + 4, y);
      y += 5;
    }
    y += 4;
  }

  if (result.recommendations.length > 0) {
    y = addPage(doc, y, 14);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Recomendações", MARGIN, y);
    y += 7;

    doc.setFontSize(9);
    for (const rec of result.recommendations) {
      y = addPage(doc, y, 14);
      doc.setFont("helvetica", "bold");
      doc.text(`${rec.icon} ${rec.title}`, MARGIN + 4, y);
      y += 4;
      doc.setFont("helvetica", "normal");
      const lines = doc.splitTextToSize(rec.body, CONTENT_W - 8);
      doc.text(lines, MARGIN + 4, y);
      y += lines.length * 4 + 4;
    }
  }

  const totalPages = doc.getNumberOfPages();
  for (let i = 1; i <= totalPages; i += 1) {
    doc.setPage(i);
    doc.setFontSize(9);
    doc.setTextColor(150, 150, 150);
    doc.text(`Página ${i} de ${totalPages}`, PAGE_W - MARGIN, 295, { align: "right" });
  }

  doc.save("cardiorisk-relatorio.pdf");
}
