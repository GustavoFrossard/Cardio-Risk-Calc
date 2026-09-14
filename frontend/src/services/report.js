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

// Cores da identidade visual do app (mesmos tokens de main.jsx, em RGB 0-255)
const COR = {
  blue: [26, 107, 240],
  blueSoft: [235, 241, 254],
  green: [14, 123, 82],
  greenSoft: [237, 250, 244],
  amber: [196, 122, 0],
  amberSoft: [255, 248, 230],
  red: [224, 49, 49],
  redSoft: [255, 240, 240],
  ink: [13, 17, 23],
  inkMid: [61, 68, 81],
  inkMuted: [139, 144, 154],
  border: [228, 231, 238],
  white: [255, 255, 255],
};

const TOM_RECOMENDACAO = {
  verde: { cor: COR.green, fundo: COR.greenSoft },
  amarelo: { cor: COR.amber, fundo: COR.amberSoft },
  vermelho: { cor: COR.red, fundo: COR.redSoft },
};

function tomDe(tipo) {
  return TOM_RECOMENDACAO[tipo] ?? TOM_RECOMENDACAO.amarelo;
}

// A fonte padrão (helvetica) do jsPDF não tem os glifos de dígito subscrito
// (₂ etc.) nem alguns símbolos — sem isso o cálculo de largura do texto
// erra e a linha corta no meio. Sanitiza pra equivalentes ASCII só no PDF,
// mantendo a tipografia bonita na tela.
function textoPdfSeguro(texto) {
  if (!texto) return texto;
  const subscritos = { "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9" };
  return texto
    .replace(/[₀₁₂₃₄₅₆₇₈₉]/g, (d) => subscritos[d])
    .replace(/≥/g, ">=")
    .replace(/≤/g, "<=");
}

function obterRotuloCirurgia(tipoCirurgia) {
  return OPCOES_CIRURGIA.find((opcao) => opcao.valor === tipoCirurgia)?.rotulo || "Não informada";
}

function adicionarPagina(doc, y, needed) {
  if (y + needed > 280) {
    doc.addPage();
    return MARGIN;
  }
  return y;
}

function estaRodandoNoWebViewReactNative() {
  return Boolean(
    typeof window !== "undefined" &&
      window.ReactNativeWebView &&
      typeof window.ReactNativeWebView.postMessage === "function",
  );
}

// ─── Ícones vetoriais simples ──────────────────────────────────────────────

function desenharCheck(doc, x, y, tamanho, cor) {
  doc.setDrawColor(...cor);
  doc.setLineWidth(0.5);
  doc.line(x, y + tamanho * 0.5, x + tamanho * 0.35, y + tamanho * 0.85);
  doc.line(x + tamanho * 0.35, y + tamanho * 0.85, x + tamanho, y + tamanho * 0.1);
}

function desenharCirculoVazio(doc, x, y, raio, cor) {
  doc.setDrawColor(...cor);
  doc.setLineWidth(0.35);
  doc.circle(x, y, raio, "S");
}

function desenharAlerta(doc, x, y, tamanho, cor) {
  doc.setFillColor(...cor);
  doc.triangle(x + tamanho / 2, y, x, y + tamanho, x + tamanho, y + tamanho, "F");
  doc.setDrawColor(...COR.white);
  doc.setLineWidth(0.5);
  doc.line(x + tamanho / 2, y + tamanho * 0.42, x + tamanho / 2, y + tamanho * 0.68);
  doc.setFillColor(...COR.white);
  doc.circle(x + tamanho / 2, y + tamanho * 0.82, 0.35, "F");
}

// ─── Linha do tempo de medicações (espelha o gráfico de bolhas da tela) ────

const TIMELINE_HASTE_BASE = 4.5;
const TIMELINE_HASTE_PASSO = 8.5;
const TIMELINE_BOLHA_H = 5.2;
const TIMELINE_GAP_MINIMO = 0.22; // fração da largura da trilha
// Duas bolhas da mesma cor exigem mais distância entre si — do contrário
// ficam parecendo o mesmo item mesmo quando os dias são diferentes.
const TIMELINE_GAP_MINIMO_MESMA_COR = 0.36;

function agruparPorDia(lista, chave) {
  const porDia = {};
  lista.forEach((m) => {
    (porDia[chave(m)] ??= []).push(m);
  });
  return porDia;
}

// Ordena por posição no eixo e, quando dois grupos vizinhos ficam próximos
// demais (bolhas colidiriam ou se confundiriam por terem a mesma cor),
// escalona o grupo seguinte para uma haste mais alta.
function disporGrupos(diasUnicos, porDia, xFn, trackW) {
  let xAnterior = null;
  let lanesAnterior = 0;
  let tipoAnterior = null;
  return diasUnicos.map((dia) => {
    const x = xFn(dia);
    const itens = porDia[dia];
    const tipoAtual = itens[0].tipo;
    const gapMinimo = trackW * (tipoAtual === tipoAnterior ? TIMELINE_GAP_MINIMO_MESMA_COR : TIMELINE_GAP_MINIMO);
    const laneBase = xAnterior != null && x - xAnterior < gapMinimo ? lanesAnterior : 0;
    xAnterior = x;
    lanesAnterior = laneBase + itens.length;
    tipoAnterior = tipoAtual;
    return { dia, x, itens, laneBase };
  });
}

const TIMELINE_BOLHA_LARGURA_MAX = 42; // mm — nomes maiores são truncados com reticências

function truncarParaLargura(doc, texto, larguraMax) {
  if (doc.getTextWidth(texto) <= larguraMax) return texto;
  let truncado = texto;
  while (truncado.length > 1 && doc.getTextWidth(`${truncado}…`) > larguraMax) {
    truncado = truncado.slice(0, -1);
  }
  return `${truncado}…`;
}

// Desenha só a haste (linha vertical) — chamada antes das bolhas do grupo
// para que a bolha sempre fique por cima e o texto nunca fique cortado.
function desenharHaste(doc, x, yBase, lane, tom, tracejado) {
  const yTopo = yBase - TIMELINE_HASTE_BASE - lane * TIMELINE_HASTE_PASSO + TIMELINE_BOLHA_H / 2;
  if (doc.setLineDashPattern) doc.setLineDashPattern(tracejado ? [0.8, 0.6] : [], 0);
  doc.setDrawColor(...tom.cor.map((c) => Math.round(c)));
  doc.setLineWidth(0.3);
  doc.line(x, yBase, x, yTopo);
  if (doc.setLineDashPattern) doc.setLineDashPattern([], 0);
}

function desenharBolha(doc, x, yBase, lane, texto, tom, tracejado) {
  const yBolha = yBase - TIMELINE_HASTE_BASE - lane * TIMELINE_HASTE_PASSO;
  doc.setFont("helvetica", tracejado ? "normal" : "bold");
  doc.setFontSize(7.2);
  const textoExibido = truncarParaLargura(doc, texto, TIMELINE_BOLHA_LARGURA_MAX);
  const largura = doc.getTextWidth(textoExibido) + 3.6;

  doc.setFillColor(...(tracejado ? COR.white : tom.fundo));
  doc.setDrawColor(...tom.cor.map((c) => Math.round(c)));
  doc.setLineWidth(0.3);
  doc.roundedRect(x - largura / 2, yBolha - TIMELINE_BOLHA_H / 2, largura, TIMELINE_BOLHA_H, 1.1, 1.1, "FD");
  doc.setTextColor(...tom.cor.map((c) => Math.round(c)));
  doc.text(textoExibido, x, yBolha + 1.2, { align: "center" });
}

function desenharLinhaTempoMedicacoes(doc, yInicial, suspensas) {
  const trackX = MARGIN;
  const trackW = CONTENT_W;

  const maxPre = Math.max(...suspensas.map((m) => m.dias_antes));
  const maxPos = Math.max(1, ...suspensas.map((m) => m.retorno_dias_depois ?? 1));
  const totalDias = maxPre + maxPos;

  // Reserva uma margem nas duas pontas da trilha para que bolhas nos dias
  // extremos não sangrem para fora da área de conteúdo.
  const inset = trackW * 0.07;
  const trackInterno = trackW - inset * 2;
  const xPre = (dia) => trackX + inset + ((maxPre - dia) / totalDias) * trackInterno;
  const xPos = (dia) => trackX + inset + ((maxPre + dia) / totalDias) * trackInterno;
  const xCirurgia = trackX + inset + (maxPre / totalDias) * trackInterno;

  const porDiaPre = agruparPorDia(suspensas, (m) => m.dias_antes);
  const diasUnicosPre = [...new Set(suspensas.map((m) => m.dias_antes))].sort((a, b) => b - a);
  const porDiaPos = agruparPorDia(suspensas, (m) => m.retorno_dias_depois ?? 1);
  const diasUnicosPos = [...new Set(suspensas.map((m) => m.retorno_dias_depois ?? 1))].sort((a, b) => a - b);

  const gruposPre = disporGrupos(diasUnicosPre, porDiaPre, xPre, trackW);
  const gruposPos = disporGrupos(diasUnicosPos, porDiaPos, xPos, trackW);

  const maxLanes = Math.max(
    1,
    ...gruposPre.map((g) => g.laneBase + g.itens.length),
    ...gruposPos.map((g) => g.laneBase + g.itens.length),
  );
  const alturaTopo = TIMELINE_HASTE_BASE + (maxLanes - 1) * TIMELINE_HASTE_PASSO + TIMELINE_BOLHA_H / 2 + 1;
  const alturaGrafico = alturaTopo + 9.5;

  const y = adicionarPagina(doc, yInicial, alturaGrafico + 6);
  const yBase = y + alturaTopo;

  doc.setDrawColor(...COR.border);
  doc.setLineWidth(0.25);
  doc.line(trackX, yBase, trackX + trackW, yBase);

  doc.setFillColor(...COR.ink);
  doc.circle(xCirurgia, yBase, 0.9, "F");

  // Rótulos do eixo (D-x, Cirurgia, D+x): quando dois ficam próximos demais,
  // alterna uma segunda linha para não sobrepor o texto.
  const TICK_GAP_MINIMO = trackW * 0.15;
  const rotulosEixo = [
    ...gruposPre.map((g) => ({ x: g.x, texto: `D-${g.dia}`, negrito: false })),
    { x: xCirurgia, texto: "Cirurgia", negrito: true },
    ...gruposPos.map((g) => ({ x: g.x, texto: `D+${g.dia}`, negrito: false })),
  ]
    .sort((a, b) => a.x - b.x)
    .reduce((acc, tick) => {
      const anterior = acc[acc.length - 1];
      const linha = anterior && tick.x - anterior.x < TICK_GAP_MINIMO ? (anterior.linha === 0 ? 1 : 0) : 0;
      acc.push({ ...tick, linha });
      return acc;
    }, []);
  for (const r of rotulosEixo) {
    doc.setFont("helvetica", r.negrito ? "bold" : "normal");
    doc.setFontSize(7.2);
    doc.setTextColor(...(r.negrito ? COR.ink : COR.inkMuted));
    doc.text(r.texto, r.x, yBase + (r.linha === 0 ? 4 : 7.5), { align: "center" });
  }

  doc.setFont("helvetica", "normal");
  doc.setTextColor(...COR.inkMuted);
  for (const grupo of gruposPre) {
    doc.setFillColor(...COR.inkMuted);
    doc.circle(grupo.x, yBase, 0.7, "F");
    // hastes primeiro — ficam atrás das bolhas para não cortar o texto
    grupo.itens.forEach((m, i) => {
      desenharHaste(doc, grupo.x, yBase, grupo.laneBase + i, tomDe(m.tipo), false);
    });
    grupo.itens.forEach((m, i) => {
      desenharBolha(doc, grupo.x, yBase, grupo.laneBase + i, m.medicamento, tomDe(m.tipo), false);
    });
  }
  for (const grupo of gruposPos) {
    doc.setDrawColor(...COR.inkMuted);
    doc.setLineWidth(0.25);
    doc.circle(grupo.x, yBase, 0.7, "S");
    grupo.itens.forEach((m, i) => {
      desenharHaste(doc, grupo.x, yBase, grupo.laneBase + i, tomDe(m.tipo), true);
    });
    grupo.itens.forEach((m, i) => {
      desenharBolha(doc, grupo.x, yBase, grupo.laneBase + i, m.medicamento, tomDe(m.tipo), true);
    });
  }

  doc.setTextColor(...COR.ink);
  return yBase + 11;
}

// ─── Relatório principal ───────────────────────────────────────────────────

export function gerarRelatorio(resultado, dados) {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const nomeIndice = resultado.indice_risco === "vsg" ? "VSG-CRI" : "RCRI";
  const rotuloCirurgia = obterRotuloCirurgia(dados.tipo_cirurgia);
  const rotuloRiscoCirurgia = ROTULOS_RISCO_CIRURGIA[resultado.risco_cirurgia] || resultado.risco_cirurgia || "Não informado";
  let y = MARGIN;

  // ─── Header ──────────────────────────────────────────────────────
  doc.setFillColor(...COR.blue);
  doc.rect(0, 0, PAGE_W, 36, "F");

  doc.setTextColor(...COR.white);
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
  doc.setTextColor(...COR.ink);

  // ─── Patient info ───────────────────────────────────────────────
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text("Dados do Paciente", MARGIN, y);
  y += 7;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  const nomePaciente = dados.nome || "Não informado";
  const idadePaciente = dados.idade != null ? `${dados.idade} anos` : "Não informada";
  doc.text(textoPdfSeguro(`Paciente: ${nomePaciente}`), MARGIN, y);
  y += 5;
  doc.text(`Idade: ${idadePaciente}`, MARGIN, y);
  y += 5;
  doc.text(textoPdfSeguro(`Cirurgia: ${rotuloCirurgia}`), MARGIN, y);
  y += 5;
  doc.text(`Risco cirúrgico: ${rotuloRiscoCirurgia}`, MARGIN, y);
  y += 5;
  doc.text(textoPdfSeguro(`Capacidade Funcional: ${resultado.mets} METs — ${resultado.rotulo_mets}`), MARGIN, y);
  y += 10;

  doc.setDrawColor(...COR.border);
  doc.line(MARGIN, y, MARGIN + CONTENT_W, y);
  y += 8;

  if (resultado.tem_condicoes_ativas) {
    y = adicionarPagina(doc, y, 20 + resultado.condicoes_ativas.length * 5);
    doc.setFillColor(...COR.redSoft);
    const boxH = 14 + resultado.condicoes_ativas.length * 5;
    doc.roundedRect(MARGIN, y - 3, CONTENT_W, boxH, 2, 2, "F");

    desenharAlerta(doc, MARGIN + 4, y - 0.5, 4.2, COR.red);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(10);
    doc.setTextColor(...COR.red);
    doc.text("Condições Cardíacas Ativas Detectadas", MARGIN + 10.5, y + 2.6);
    y += 9;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(...COR.ink);
    for (const cond of resultado.condicoes_ativas) {
      doc.text(textoPdfSeguro(`•  ${cond}`), MARGIN + 6, y);
      y += 5;
    }
    y += 6;
  }

  y = adicionarPagina(doc, y, 30);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.setTextColor(...COR.ink);
  doc.text(`Resultado — Índice ${nomeIndice}`, MARGIN, y);
  y += 8;

  const tomRisco =
    resultado.classe_risco === "baixo" ? { cor: COR.green, fundo: COR.greenSoft } :
    resultado.classe_risco === "intermediario" ? { cor: COR.amber, fundo: COR.amberSoft } :
    { cor: COR.red, fundo: COR.redSoft };

  doc.setFillColor(...tomRisco.fundo);
  doc.setDrawColor(...tomRisco.cor);
  doc.setLineWidth(0.4);
  doc.roundedRect(MARGIN, y - 3, CONTENT_W, 18, 2, 2, "FD");

  if (resultado.classe_risco === "baixo") {
    doc.setDrawColor(...COR.white);
    doc.setFillColor(...tomRisco.cor);
    doc.circle(MARGIN + 7, y + 6, 3.4, "F");
    desenharCheck(doc, MARGIN + 5.1, y + 4.1, 3.8, COR.white);
  } else {
    desenharAlerta(doc, MARGIN + 4.5, y + 2.3, 5, tomRisco.cor);
  }

  doc.setTextColor(...tomRisco.cor);
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text(`${resultado.rotulo_risco}`, MARGIN + 15, y + 7);
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.text(`Score: ${resultado.pontuacao} pt${resultado.pontuacao !== 1 ? "s" : ""}`, MARGIN + CONTENT_W - 4, y + 7, { align: "right" });

  y += 22;
  doc.setTextColor(...COR.ink);

  if (resultado.fatores_risco.length > 0) {
    y = adicionarPagina(doc, y, 10 + resultado.fatores_risco.length * 5.5);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Fatores de Risco Identificados", MARGIN, y);
    y += 7;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    for (const fator of resultado.fatores_risco) {
      y = adicionarPagina(doc, y, 6);
      desenharCirculoVazio(doc, MARGIN + 4.5, y - 1.3, 1.2, COR.inkMuted);
      doc.setTextColor(...COR.inkMid);
      doc.text(textoPdfSeguro(fator), MARGIN + 8, y);
      y += 5.5;
    }
    y += 3;
    doc.setTextColor(...COR.ink);
  }

  if (resultado.orientacoes_medicacao.length > 0) {
    y = adicionarPagina(doc, y, 14);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Manejo de Medicamentos", MARGIN, y);
    y += 4;

    const suspensas = resultado.orientacoes_medicacao.filter((m) => m.dias_antes != null);
    if (suspensas.length > 0) {
      y += 4;
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7.5);
      doc.setTextColor(...COR.inkMuted);
      doc.text("Dias em relação à cirurgia — tracejado indica retorno da medicação", MARGIN, y);
      y += 5;
      y = desenharLinhaTempoMedicacoes(doc, y, suspensas);
      doc.setTextColor(...COR.ink);
    } else {
      y += 3;
    }

    doc.setFontSize(9);
    for (const med of resultado.orientacoes_medicacao) {
      const tom = tomDe(med.tipo);
      y = adicionarPagina(doc, y, 14);
      doc.setDrawColor(...tom.cor);
      doc.setLineWidth(0.8);
      doc.line(MARGIN, y - 3.2, MARGIN, y + 8);
      doc.setFont("helvetica", "bold");
      doc.setTextColor(...COR.ink);
      doc.text(`${med.medicamento}`, MARGIN + 4, y);
      const larguraNome = doc.getTextWidth(med.medicamento);
      doc.setTextColor(...tom.cor);
      doc.setFont("helvetica", "normal");
      doc.text(`  —  ${med.acao}`, MARGIN + 4 + larguraNome, y);
      y += 4;
      doc.setFont("helvetica", "normal");
      doc.setTextColor(...COR.inkMid);
      const lines = doc.splitTextToSize(textoPdfSeguro(med.detalhe), CONTENT_W - 8);
      doc.text(lines, MARGIN + 4, y);
      y += lines.length * 4 + 5;
    }
    doc.setTextColor(...COR.ink);
    y += 2;
  }

  if (resultado.exames_recomendados.length > 0) {
    y = adicionarPagina(doc, y, 10 + resultado.exames_recomendados.length * 5);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Exames Recomendados", MARGIN, y);
    y += 7;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    for (const exame of resultado.exames_recomendados) {
      y = adicionarPagina(doc, y, 6);
      desenharCheck(doc, MARGIN + 3.4, y - 2.6, 3, COR.blue);
      doc.setTextColor(...COR.inkMid);
      doc.text(textoPdfSeguro(exame), MARGIN + 8, y);
      y += 5.5;
    }
    y += 3;
    doc.setTextColor(...COR.ink);
  }

  if (resultado.recomendacoes.length > 0) {
    y = adicionarPagina(doc, y, 14);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text("Recomendações", MARGIN, y);
    y += 7;

    doc.setFontSize(9);
    for (const rec of resultado.recomendacoes) {
      const tom = tomDe(rec.tipo);
      y = adicionarPagina(doc, y, 14);
      doc.setDrawColor(...tom.cor);
      doc.setLineWidth(0.8);
      doc.line(MARGIN, y - 3.2, MARGIN, y + 8);
      doc.setFont("helvetica", "bold");
      doc.setTextColor(...COR.ink);
      doc.text(textoPdfSeguro(`${rec.titulo}`), MARGIN + 4, y);
      y += 4;
      doc.setFont("helvetica", "normal");
      doc.setTextColor(...COR.inkMid);
      const lines = doc.splitTextToSize(textoPdfSeguro(rec.corpo), CONTENT_W - 8);
      doc.text(lines, MARGIN + 4, y);
      y += lines.length * 4 + 5;
    }
    doc.setTextColor(...COR.ink);
  }

  const totalPages = doc.getNumberOfPages();
  for (let i = 1; i <= totalPages; i += 1) {
    doc.setPage(i);
    doc.setFontSize(9);
    doc.setTextColor(...COR.inkMuted);
    doc.text(`Página ${i} de ${totalPages}`, PAGE_W - MARGIN, 295, { align: "right" });
  }

  const nomeSafe = dados.nome ? dados.nome.trim() : "Paciente";
  const dateObj = new Date();
  const dateForFile = `${dateObj.getDate().toString().padStart(2, '0')}-${(dateObj.getMonth() + 1).toString().padStart(2, '0')}-${dateObj.getFullYear()}`;
  const filename = `CardioRisk - ${nomeSafe} - ${dateForFile}.pdf`;

  if (estaRodandoNoWebViewReactNative()) {
    const dataUri = doc.output("datauristring");
    const base64 = dataUri.includes(",") ? dataUri.split(",")[1] : "";
    window.ReactNativeWebView.postMessage(
      JSON.stringify({ type: "pdf-base64", filename, base64 }),
    );
    return;
  }

  doc.save(filename);
}
