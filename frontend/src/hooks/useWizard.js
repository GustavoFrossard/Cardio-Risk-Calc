import { useState, useCallback, useEffect, useRef } from "react";
import { defaultPatientData, WIZARD_STEPS } from "../types";
import { api } from "../services/api";

const STORAGE_KEY = "cardiorisk_wizard_v1";

function loadSaved() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    // Ignore saves older than 48h
    if (Date.now() - (parsed.savedAt ?? 0) > 48 * 60 * 60 * 1000) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function saveToDisk(step, data) {
  try {
    // Don't persist empty first-step state
    if (step === 1 && !data.name && data.age === undefined) return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ step, data, savedAt: Date.now() }));
  } catch {}
}

export function useAssistente() {
  const savedRef = useRef(loadSaved());
  const [hasSavedData] = useState(() => savedRef.current !== null);

  const [currentStep, setCurrentStep] = useState(1);
  const [highestStep, setHighestStep] = useState(1);
  const [formData, setFormData] = useState(defaultPatientData);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [nlpResult, setNlpResult] = useState(null);
  const [error, setError] = useState(null);

  const totalSteps = WIZARD_STEPS.length;

  const updateField = useCallback((key, value) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  }, []);

  // Persist to localStorage whenever step or data changes
  useEffect(() => {
    if (currentStep < 4) saveToDisk(currentStep, formData);
  }, [currentStep, formData]);

  const resumeSaved = useCallback(() => {
    if (!savedRef.current) return;
    setFormData(savedRef.current.data);
    const step = savedRef.current.step ?? 1;
    setCurrentStep(step);
    setHighestStep(step);
  }, []);

  const analyzeClinicalText = useCallback(async (text) => {
    setIsAnalyzing(true);
    setError(null);
    try {
      const res = await api.analyzeClinicalCase(text, formData);
      setNlpResult(res);
      if (res?.autofill && typeof res.autofill === "object") {
        setFormData((prev) => ({ ...prev, ...res.autofill }));
      }
      return res;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao analisar texto clínico.");
      return null;
    } finally {
      setIsAnalyzing(false);
    }
  }, [formData]);

  const submitToApi = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.calculateRisk(formData);
      setResult(res);
      setCurrentStep(4);
      setHighestStep(4);
      try { localStorage.removeItem(STORAGE_KEY); } catch {}
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Erro ao calcular risco. Verifique a conexão com o servidor.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [formData]);

  const goNext = useCallback(() => {
    if (currentStep === 3) {
      submitToApi();
      return;
    }
    if (currentStep < totalSteps) {
      const next = currentStep + 1;
      setCurrentStep(next);
      setHighestStep((h) => Math.max(h, next));
    }
  }, [currentStep, totalSteps, submitToApi]);

  const goBack = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep((s) => (s === 4 ? 3 : s - 1));
    }
  }, [currentStep]);

  const goToStep = useCallback((step) => {
    if (step >= 1 && step < 4 && step <= highestStep) {
      setCurrentStep(step);
    }
  }, [highestStep]);

  const reset = useCallback(() => {
    setCurrentStep(1);
    setHighestStep(1);
    setFormData(defaultPatientData);
    setResult(null);
    setNlpResult(null);
    setError(null);
    try { localStorage.removeItem(STORAGE_KEY); } catch {}
  }, []);

  return {
    currentStep,
    totalSteps,
    highestStep,
    hasSavedData,
    formData,
    result,
    isLoading,
    isAnalyzing,
    nlpResult,
    error,
    updateField,
    analyzeClinicalText,
    goNext,
    goBack,
    goToStep,
    resumeSaved,
    reset,
  };
}
