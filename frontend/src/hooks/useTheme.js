import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "cardiorisk-theme";

function obterTemaDoSistema() {
  return window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ? "dark" : "light";
}

function obterTemaInicial() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    /* localStorage indisponível — cai no tema do sistema */
  }
  return obterTemaDoSistema();
}

/**
 * Gerencia o tema (claro/escuro) com persistência em localStorage.
 * Aplica o atributo data-theme no <html>, que sobrepõe o prefers-color-scheme.
 */
export function useTheme() {
  const [theme, setTheme] = useState(obterTemaInicial);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      /* ignora falha de persistência */
    }
  }, [theme]);

  const toggle = useCallback(() => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  return { theme, toggle };
}
