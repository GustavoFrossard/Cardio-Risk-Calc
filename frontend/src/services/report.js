import jsPDF from "jspdf";
import { OPCOES_CIRURGIA } from "../types";

const MARGIN = 20;
const PAGE_W = 210;
const CONTENT_W = PAGE_W - MARGIN * 2;
const ROTULOS_RISCO_CIRURGIA = {
  baixo: "Baixo",
  intermediario: "Intermediário",
  alto: "Alto",
};

function getRotuloCirurgia(tipoCirurgia) {
  return OPCOES_CIRURGIA.find((opcao) => opcao.valor === tipoCirurgia)?.rotulo || "Não informada";
}

function addPage(doc, y, needed) {
  if (y + needed > 280) {
    doc.addPage();
    return MARGIN;
  }
  return y;
}

function isRunningInsideReactNativeWebView() {
  return Boolean(
    typeof window !== "undefined" &&
      window.ReactNativeWebView &&
      typeof window.ReactNativeWebView.postMessage === "function",
  );
}

export function gerarRelatorio(resultado, dados) {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const nomeIndice = resultado.indice_risco === "vsg" ? "VSG-CRI" : "RCRI";
  const rotuloCirurgia = getRotuloCirurgia(dados.tipo_cirurgia);
  const rotuloRiscoCirurgia = ROTULOS_RISCO_CIRURGIA[resultado.risco_cirurgia] || resultado.risco_cirurgia || "Não informado";
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
  const nomePaciente = dados.nome || "Não informado";
  const idadePaciente = dados.idade != null ? `${dados.idade} anos` : "Não informada";
  doc.text(`Paciente: ${nomePaciente}`, MARGIN, y);
  y += 5;
  doc.text(`Idade: ${idadePaciente}`, MARGIN, y);
  y += 5;
  doc.text(`Cirurgia: ${rotuloCirurgia}`, MARGIN, y);
  y += 5;
  doc.text(`Risco cirúrgico: ${rotuloRiscoCirurgia}`, MARGIN, y);
  y += 5;
  doc.text(`Capacidade Funcional: ${resultado.mets} METs — ${resultado.rotulo_mets}`, MARGIN, y);
  y += 10;

  doc.setDrawColor(200, 200, 200);
  doc.line(MARGIN, y, MARGIN + CONTENT_W, y);
  y += 8;

  if (resultado.tem_condicoes_ativas) {
    y = addPage(doc, y, 20 + resultado.condicoes_ativas.length * 5);
    doc.setFillColor(254, 226, 226);
    const boxH = 12 + resultado.condicoes_ativas.length * 5;
    doc.roundedRect(MARGIN, y - 3, CONTENT_W, boxH, 2, 2, "F");

    doc.setFont("helvetica", "bold");
    doc.setFontSize(10);
    doc.setTextColor(185, 28, 28);
    doc.text("[!] CONDICOES CARDIACAS ATIVAS DETECTADAS", MARGIN + 4, y + 3);
    y += 8;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    for (const cond of resultado.condicoes_ativas) {
      doc.text(`• ${cond}`, MARGIN + 6, y);
      y += 5;
    }
    y += 6;
    doc.setTextColor(30, 30, 30);
  }

  y = addPage(doc, y, 30);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.text(`Resultado — Índice ${nomeIndice}`, MARGIN, y);
  y += 8;

  const corRisco =
    resultado.classe_risco === "baixo" ? [22, 163, 74] :
    resultado.classe_risco === "intermediario" ? [202, 138, 4] :
    [220, 38, 38];

  doc.setFillColor(corRisco[0], corRisco[1], corRisco[2]);
  doc.roundedRect(MARGIN, y - 3, CONTENT_W, 18, 2, 2, "F");

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text(`${resultado.rotulo_risco}`, MARGIN + 6, y + 7);
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.text(`Score: ${resultado.pontuacao} pt${resultado.pontuacao !== 1 ? "s" : ""}`, MARGIN + CONTENT_W - 4, y + 7, { align: "right" });

  y += 22;
  doc.setTextColor(30, 30, 30);

  if (resultado.fatores_risco.length > 0) {
    y = addPage(doc, y, 10 + resultado.fatores_risco.length * 5);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Fatores de Risco Identificados", MARGIN, y);
    y += 6;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    for (const fator of resultado.fatores_risco) {
      y = addPage(doc, y, 6);
      doc.text(`• ${fator}`, MARGIN + 4, y);
      y += 5;
    }
    y += 4;
  }

  if (resultado.orientacoes_medicacao.length > 0) {
    y = addPage(doc, y, 14);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Manejo de Medicamentos", MARGIN, y);
    y += 7;

    doc.setFontSize(9);
    for (const med of resultado.orientacoes_medicacao) {
      y = addPage(doc, y, 14);
      doc.setFont("helvetica", "bold");
      doc.text(`${med.medicamento} — ${med.acao}`, MARGIN + 4, y);
      y += 4;
      doc.setFont("helvetica", "normal");
      const lines = doc.splitTextToSize(med.detalhe, CONTENT_W - 8);
      doc.text(lines, MARGIN + 4, y);
      y += lines.length * 4 + 4;
    }
    y += 2;
  }

  if (resultado.exames_recomendados.length > 0) {
    y = addPage(doc, y, 10 + resultado.exames_recomendados.length * 5);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Exames Recomendados", MARGIN, y);
    y += 6;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    for (const exame of resultado.exames_recomendados) {
      y = addPage(doc, y, 6);
      doc.text(`• ${exame}`, MARGIN + 4, y);
      y += 5;
    }
    y += 4;
  }

  if (resultado.recomendacoes.length > 0) {
    y = addPage(doc, y, 14);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Recomendações", MARGIN, y);
    y += 7;

    doc.setFontSize(9);
    for (const rec of resultado.recomendacoes) {
      y = addPage(doc, y, 14);
      doc.setFont("helvetica", "bold");
      doc.text(`${rec.titulo}`, MARGIN + 4, y);
      y += 4;
      doc.setFont("helvetica", "normal");
      const lines = doc.splitTextToSize(rec.corpo, CONTENT_W - 8);
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

  const nomeSafe = dados.nome ? dados.nome.trim() : "Paciente";
  const dateObj = new Date();
  const dateForFile = `${dateObj.getDate().toString().padStart(2, '0')}-${(dateObj.getMonth() + 1).toString().padStart(2, '0')}-${dateObj.getFullYear()}`;
  const filename = `CardioRisk - ${nomeSafe} - ${dateForFile}.pdf`;

  if (isRunningInsideReactNativeWebView()) {
    const dataUri = doc.output("datauristring");
    const base64 = dataUri.includes(",") ? dataUri.split(",")[1] : "";
    window.ReactNativeWebView.postMessage(
      JSON.stringify({ type: "pdf-base64", filename, base64 }),
    );
    return;
  }

  doc.save(filename);
}
