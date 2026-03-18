// ─── Surgery Risk Types ───────────────────────────────────────────────────────

export type SurgeryRisk = "low" | "intermediate" | "high";
export type RiskClass = "low" | "intermediate" | "high";
export type RecommendationType = "green" | "amber" | "red";

// ─── Surgery Options (Tabela 3 - Diretriz) ───────────────────────────────────

export interface SurgeryOption {
  value: string;
  label: string;
  risk: SurgeryRisk;
  vascular: boolean;
}

export const SURGERY_OPTIONS: SurgeryOption[] = [
  // Baixo Risco (<1%)
  { value: "breast", label: "Mama", risk: "low", vascular: false },
  { value: "dental", label: "Procedimentos dentários", risk: "low", vascular: false },
  { value: "thyroid", label: "Tireoide", risk: "low", vascular: false },
  { value: "eye", label: "Ocular", risk: "low", vascular: false },
  { value: "gynecologic_minor", label: "Ginecológica minor", risk: "low", vascular: false },
  { value: "orthopedic_minor", label: "Ortopédica minor (menisco)", risk: "low", vascular: false },
  { value: "reconstructive", label: "Reconstrutiva", risk: "low", vascular: false },
  { value: "superficial", label: "Superfície", risk: "low", vascular: false },
  { value: "urologic_minor", label: "Urológica minor (RTU)", risk: "low", vascular: false },
  { value: "vats_minor", label: "VATS minor", risk: "low", vascular: false },
  // Risco Intermediário (1–5%)
  { value: "carotid_asymptomatic", label: "Carótida assintomática", risk: "intermediate", vascular: true },
  { value: "carotid_endarterectomy", label: "Endarterectomia carótida (sintomática)", risk: "intermediate", vascular: true },
  { value: "peripheral_angioplasty", label: "Angioplastia arterial periférica", risk: "intermediate", vascular: true },
  { value: "endovascular_aortic", label: "Aneurisma de aorta endovascular", risk: "intermediate", vascular: true },
  { value: "head_neck", label: "Cabeça e pescoço", risk: "intermediate", vascular: false },
  { value: "intraperitoneal", label: "Intraperitoneal (colecistectomia, hérnia hiatal, esplenectomia)", risk: "intermediate", vascular: false },
  { value: "intrathoracic", label: "Intratorácica non-major", risk: "intermediate", vascular: false },
  { value: "neurologic", label: "Neurológica", risk: "intermediate", vascular: false },
  { value: "orthopedic_major", label: "Ortopédica major", risk: "intermediate", vascular: false },
  { value: "renal_transplant", label: "Transplante renal", risk: "intermediate", vascular: false },
  { value: "urologic_major", label: "Urológica major", risk: "intermediate", vascular: false },
  { value: "gynecologic_major", label: "Ginecológica major", risk: "intermediate", vascular: false },
  // Alto Risco (>5%)
  { value: "aortic_vascular_major", label: "Aorta e vascular major", risk: "high", vascular: true },
  { value: "peripheral_open", label: "Revascularização periférica aberta (isquemia aguda) / amputação", risk: "high", vascular: true },
  { value: "carotid_angioplasty", label: "Angioplastia carótida (sintomática)", risk: "high", vascular: true },
  { value: "adrenal_resection", label: "Ressecção adrenal", risk: "high", vascular: false },
  { value: "pancreatic", label: "Pancreática", risk: "high", vascular: false },
  { value: "liver_biliary", label: "Fígado e vias biliares", risk: "high", vascular: false },
  { value: "esophagectomy", label: "Esofagectomia", risk: "high", vascular: false },
  { value: "pneumectomy", label: "Pneumectomia (VATS ou aberta)", risk: "high", vascular: false },
  { value: "lung_transplant", label: "Transplante pulmonar", risk: "high", vascular: false },
  { value: "liver_transplant", label: "Transplante hepático", risk: "high", vascular: false },
  { value: "total_cystectomy", label: "Cistectomia total", risk: "intermediate", vascular: false },
  { value: "bowel_perforation", label: "Reparo de perfuração intestinal", risk: "high", vascular: false },
];

// ─── Functional Capacity Questionnaire ────────────────────────────────────────

export interface FunctionalQuestion {
  id: string;
  label: string;
  mets: number;
}

export const FUNCTIONAL_QUESTIONS: FunctionalQuestion[] = [
  { id: "housework_light", label: "Fazer trabalhos leves em casa, como juntar o lixo ou lavar a louça?", mets: 2.7 },
  { id: "self_care", label: "Cuidar de si mesmo: vestir-se, alimentar-se, tomar banho?", mets: 2.75 },
  { id: "walk_flat", label: "Caminhar uma quadra ou duas, no plano?", mets: 2.75 },
  { id: "housework_moderate", label: "Fazer trabalhos moderados em casa, como passar o aspirador de pó, varrer o chão ou guardar/carregar mantimentos?", mets: 3.5 },
  { id: "climb_stairs", label: "Subir um lance de escadas ou caminhar em uma subida?", mets: 5.5 },
  { id: "yard_work", label: "Fazer trabalhos no jardim/quintal, como usar o rastelo, juntar folhas ou usar a máquina de cortar grama?", mets: 4.5 },
  { id: "sexual_activity", label: "Ter atividade sexual?", mets: 5.25 },
  { id: "recreation_moderate", label: "Participar de atividades recreacionais moderadas, como jogar boliche, dançar, jogar tênis em dupla?", mets: 6 },
  { id: "sports", label: "Participar de atividades esportivas, como natação, ou tênis individual, ou futebol?", mets: 7.5 },
  { id: "housework_heavy", label: "Fazer trabalhos pesados em casa, como esfregar/lavar o piso, ou levantar ou deslocar móveis pesados?", mets: 8 },
  { id: "run_short", label: "Correr uma distância curta?", mets: 8 },
];

// ─── Patient Form Data ────────────────────────────────────────────────────────

export interface PatientData {
  // === Step 1: Dados do Paciente ===
  name?: string;
  age?: number;

  // Comorbidades
  obesity: boolean;
  known_hf: boolean;
  known_valvular_disease: boolean;
  known_cad: boolean;

  // Medicamentos
  uses_aas: boolean;
  aas_prevention: "primary" | "secondary" | "";
  uses_clopidogrel: boolean;
  uses_ticagrelor: boolean;
  uses_prasugrel: boolean;
  uses_warfarin: boolean;
  warfarin_indication: "af" | "vte" | "mechanical_valve" | "rheumatic" | "";
  warfarin_chadsvasc?: number;
  warfarin_stroke_3m: boolean;
  warfarin_vte_timing: "recent" | "3_12m" | "over_12m" | "";
  warfarin_thrombophilia: "severe" | "mild" | "none" | "";
  warfarin_active_neoplasia: boolean;

  // Capacidade funcional
  functional_activities: string[];
  mets: number;

  // === Step 2: Cirurgia e Condições Ativas ===
  surgery_type: string;
  surgery_risk: SurgeryRisk | "";
  is_vascular: boolean;

  // Condições cardiovasculares graves (Tabela 2)
  cv_acute_coronary: boolean;
  cv_unstable_aortic: boolean;
  cv_acute_pulmonary_edema: boolean;
  cv_cardiogenic_shock: boolean;
  cv_hf_nyha_3_4: boolean;
  cv_angina_ccs_3_4: boolean;
  cv_severe_arrhythmia: boolean;
  cv_uncontrolled_hypertension: boolean;
  cv_af_high_rate: boolean;
  cv_pulmonary_hypertension: boolean;
  cv_severe_valvular: boolean;

  // === Step 3: Índice de Risco ===

  // RCRI (Lee - cirurgia não vascular)
  rcri_high_risk_surgery: boolean;
  rcri_ischemic_heart: boolean;
  rcri_heart_failure: boolean;
  rcri_cerebrovascular: boolean;
  rcri_insulin_diabetes: boolean;
  rcri_creatinine_above_2: boolean;

  // VSG-CRI (cirurgia vascular - Tabela 6)
  vsg_age_range: "" | "lt60" | "60_69" | "70_79" | "gte80";
  vsg_cad: boolean;
  vsg_chf: boolean;
  vsg_copd: boolean;
  vsg_creatinine_over_1_8: boolean;
  vsg_smoking: boolean;
  vsg_insulin_diabetes: boolean;
  vsg_chronic_beta_blocker: boolean;
  vsg_prior_revasc: boolean;
}

// ─── API Response ─────────────────────────────────────────────────────────────

export interface Recommendation {
  type: RecommendationType;
  icon: string;
  title: string;
  body: string;
}

export interface MedicationAdvice {
  medication: string;
  action: string;
  detail: string;
  type: RecommendationType;
}

export interface RiskResult {
  risk_index: "rcri" | "vsg";
  score: number;
  score_class: string;
  mace_risk_pct: number;
  risk_class: RiskClass;
  risk_label: string;

  has_active_conditions: boolean;
  active_conditions: string[];

  criteria_met: string[];
  risk_factors: string[];

  recommendations: Recommendation[];
  medication_advice: MedicationAdvice[];
  recommended_exams: string[];

  mets: number;
  mets_label: string;
  surgery_type: string;
  surgery_risk: string;
  surgery_label: string;
  is_vascular: boolean;
  functional_capacity_adequate: boolean;
}

// ─── Wizard Steps ─────────────────────────────────────────────────────────────

export interface WizardStep {
  id: number;
  title: string;
  subtitle?: string;
}

export const WIZARD_STEPS: WizardStep[] = [
  { id: 1, title: "Dados do Paciente", subtitle: "Informações gerais, comorbidades e medicamentos" },
  { id: 2, title: "Cirurgia e Condições Ativas", subtitle: "Procedimento e condições cardiovasculares" },
  { id: 3, title: "Índice de Risco", subtitle: "RCRI ou VSG conforme tipo cirúrgico" },
  { id: 4, title: "Resultado", subtitle: "Relatório e recomendações" },
];

// ─── Default Form State ───────────────────────────────────────────────────────

export const defaultPatientData: PatientData = {
  name: "",
  age: undefined,
  obesity: false,
  known_hf: false,
  known_valvular_disease: false,
  known_cad: false,
  uses_aas: false,
  aas_prevention: "",
  uses_clopidogrel: false,
  uses_ticagrelor: false,
  uses_prasugrel: false,
  uses_warfarin: false,
  warfarin_indication: "",
  warfarin_chadsvasc: undefined,
  warfarin_stroke_3m: false,
  warfarin_vte_timing: "",
  warfarin_thrombophilia: "",
  warfarin_active_neoplasia: false,
  functional_activities: [],
  mets: 1,
  surgery_type: "",
  surgery_risk: "",
  is_vascular: false,
  cv_acute_coronary: false,
  cv_unstable_aortic: false,
  cv_acute_pulmonary_edema: false,
  cv_cardiogenic_shock: false,
  cv_hf_nyha_3_4: false,
  cv_angina_ccs_3_4: false,
  cv_severe_arrhythmia: false,
  cv_uncontrolled_hypertension: false,
  cv_af_high_rate: false,
  cv_pulmonary_hypertension: false,
  cv_severe_valvular: false,
  rcri_high_risk_surgery: false,
  rcri_ischemic_heart: false,
  rcri_heart_failure: false,
  rcri_cerebrovascular: false,
  rcri_insulin_diabetes: false,
  rcri_creatinine_above_2: false,
  vsg_age_range: "",
  vsg_cad: false,
  vsg_chf: false,
  vsg_copd: false,
  vsg_creatinine_over_1_8: false,
  vsg_smoking: false,
  vsg_insulin_diabetes: false,
  vsg_chronic_beta_blocker: false,
  vsg_prior_revasc: false,
};
