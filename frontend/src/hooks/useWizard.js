import { useState, useCallback } from "react";
import { defaultPatientData, WIZARD_STEPS } from "../types";
import { api } from "../services/api";

export function useWizard() {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState(defaultPatientData);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const totalSteps = WIZARD_STEPS.length;

  const updateField = useCallback((key, value) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  }, []);

  const submitToApi = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.calculateRisk(formData);
      setResult(res);
      setCurrentStep(4);
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
      setCurrentStep((s) => s + 1);
    }
  }, [currentStep, totalSteps, submitToApi]);

  const goBack = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep((s) => (s === 4 ? 3 : s - 1));
    }
  }, [currentStep]);

  const reset = useCallback(() => {
    setCurrentStep(1);
    setFormData(defaultPatientData);
    setResult(null);
    setError(null);
  }, []);

  return {
    currentStep,
    totalSteps,
    formData,
    result,
    isLoading,
    error,
    updateField,
    goNext,
    goBack,
    reset,
  };
}
