import { COMORBIDADES, MEDICAMENTOS, OPCOES_CIRURGIA } from "../types";

export function resumirPaciente(dados) {
  return {
    idade: dados.idade ?? null,
    mets: dados.mets ?? null,
  };
}

export function resumirCirurgia(dados) {
  const opcao = OPCOES_CIRURGIA.find((o) => o.valor === dados.tipo_cirurgia);
  return {
    definida: Boolean(opcao),
    rotulo: opcao?.rotulo ?? null,
    risco: opcao?.risco ?? dados.risco_cirurgia ?? null,
  };
}

export function resumirComorbidades(dados) {
  return COMORBIDADES.filter((c) => Boolean(dados[c.key])).map((c) => c.rotulo);
}

export function resumirMedicamentos(dados) {
  return MEDICAMENTOS.filter((m) => Boolean(dados[m.key])).map((m) => m.rotulo);
}

export const ROTULO_RISCO_CIRURGIA = {
  baixo: "Baixo",
  intermediario: "Intermediário",
  alto: "Alto",
};
