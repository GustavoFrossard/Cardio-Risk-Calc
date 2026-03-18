import { useState, useCallback } from "react";
import type { PatientData, RiskResult } from "../types";
import { defaultPatientData, WIZARD_STEPS } from "../types";
import { api } from "../services/api";

interface UseWizardReturn {
  currentStep: number;
  totalSteps: number;
  formData: PatientData;
  result: RiskResult | null;
  isLoading: boolean;
  error: string | null;
  updateField: <K extends keyof PatientData>(key: K, value: PatientData[K]) => void;
  goNext: () => void;
  goBack: () => void;
  reset: () => void;
}

export function useWizard(): UseWizardReturn {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<PatientData>(defaultPatientData);
  const [result, setResult] = useState<RiskResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const totalSteps = WIZARD_STEPS.length;

  const updateField = useCallback(
    <K extends keyof PatientData>(key: K, value: PatientData[K]) => {
      setFormData((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

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
      // If going back from results, go to step 3
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
