import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "cardiorisk-theme";

function getSystemTheme() {
  return window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ? "dark" : "light";
}

function getInitialTheme() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    /* localStorage indisponível — cai no tema do sistema */
  }
  return getSystemTheme();
}

/**
 * Gerencia o tema (claro/escuro) com persistência em localStorage.
 * Aplica o atributo data-theme no <html>, que sobrepõe o prefers-color-scheme.
 */
export function useTheme() {
  const [theme, setTheme] = useState(getInitialTheme);

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
