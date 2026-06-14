import { useState, useCallback, useEffect, useRef } from "react";
import { dadosPacienteInicial, ETAPAS_WIZARD } from "../types";
import { api } from "../services/api";

const STORAGE_KEY = "cardiorisk_wizard_v1";

function loadSaved() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    // Ignorar saves com mais de 48h
    if (Date.now() - (parsed.savedAt ?? 0) > 48 * 60 * 60 * 1000) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function saveToDisk(etapa, dados) {
  try {
    // Não persistir estado vazio da primeira etapa
    if (etapa === 1 && !dados.nome && dados.idade === undefined) return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ etapa, dados, savedAt: Date.now() }));
  } catch {}
}

export function useAssistente() {
  const savedRef = useRef(loadSaved());
  const [temDadosSalvos] = useState(() => savedRef.current !== null);

  const [etapaAtual, setEtapaAtual] = useState(1);
  const [maiorEtapa, setMaiorEtapa] = useState(1);
  const [dadosFormulario, setDadosFormulario] = useState(dadosPacienteInicial);
  const [resultado, setResultado] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [analisando, setAnalisando] = useState(false);
  const [resultadoNlp, setResultadoNlp] = useState(null);
  const [error, setError] = useState(null);

  const totalEtapas = ETAPAS_WIZARD.length;

  const atualizarCampo = useCallback((key, value) => {
    setDadosFormulario((prev) => ({ ...prev, [key]: value }));
  }, []);

  // Persistir no localStorage sempre que a etapa ou os dados mudarem
  useEffect(() => {
    if (etapaAtual < 4) saveToDisk(etapaAtual, dadosFormulario);
  }, [etapaAtual, dadosFormulario]);

  const retomar = useCallback(() => {
    if (!savedRef.current) return;
    setDadosFormulario(savedRef.current.dados);
    const etapa = savedRef.current.etapa ?? 1;
    setEtapaAtual(etapa);
    setMaiorEtapa(etapa);
  }, []);

  const analisarTextoClinico = useCallback(async (text) => {
    setAnalisando(true);
    setError(null);
    try {
      const res = await api.analisarCasoClinico(text, dadosFormulario);
      setResultadoNlp(res);
      if (res?.autofill && typeof res.autofill === "object") {
        setDadosFormulario((prev) => ({ ...prev, ...res.autofill }));
      }
      return res;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao analisar texto clínico.");
      return null;
    } finally {
      setAnalisando(false);
    }
  }, [dadosFormulario]);

  const submitToApi = useCallback(async () => {
    setCarregando(true);
    setError(null);
    try {
      const res = await api.calcularRisco(dadosFormulario);
      setResultado(res);
      setEtapaAtual(4);
      setMaiorEtapa(4);
      try { localStorage.removeItem(STORAGE_KEY); } catch {}
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Erro ao calcular risco. Verifique a conexão com o servidor.",
      );
    } finally {
      setCarregando(false);
    }
  }, [dadosFormulario]);

  const avancar = useCallback(() => {
    if (etapaAtual === 3) {
      submitToApi();
      return;
    }
    if (etapaAtual < totalEtapas) {
      const prox = etapaAtual + 1;
      setEtapaAtual(prox);
      setMaiorEtapa((h) => Math.max(h, prox));
    }
  }, [etapaAtual, totalEtapas, submitToApi]);

  const voltar = useCallback(() => {
    if (etapaAtual > 1) {
      setEtapaAtual((s) => (s === 4 ? 3 : s - 1));
    }
  }, [etapaAtual]);

  const irParaEtapa = useCallback((etapa) => {
    if (etapa >= 1 && etapa < 4 && etapa <= maiorEtapa) {
      setEtapaAtual(etapa);
    }
  }, [maiorEtapa]);

  const reiniciar = useCallback(() => {
    setEtapaAtual(1);
    setMaiorEtapa(1);
    setDadosFormulario(dadosPacienteInicial);
    setResultado(null);
    setResultadoNlp(null);
    setError(null);
    try { localStorage.removeItem(STORAGE_KEY); } catch {}
  }, []);

  return {
    etapaAtual,
    totalEtapas,
    maiorEtapa,
    temDadosSalvos,
    dadosFormulario,
    resultado,
    carregando,
    analisando,
    resultadoNlp,
    error,
    atualizarCampo,
    analisarTextoClinico,
    avancar,
    voltar,
    irParaEtapa,
    retomar,
    reiniciar,
  };
}
