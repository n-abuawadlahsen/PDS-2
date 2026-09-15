export const THEMES = ["institucional", "azul", "verde"] as const;
export type ThemeName = (typeof THEMES)[number];
export const DEFAULT_THEME: ThemeName = "institucional";
export const THEME_STORAGE_KEY = "pds2.apariencia";
export const THEME_LABELS: Record<ThemeName, string> = {
  institucional: "Rojo institucional",
  azul: "Azul académico",
  verde: "Verde sobrio",
};

export function validarTema(value: unknown): ThemeName {
  return THEMES.includes(value as ThemeName)
    ? (value as ThemeName)
    : DEFAULT_THEME;
}
/** La preferencia visual es el único dato que esta aplicación guarda aquí. */
export function aplicarTema(value: unknown, persistir = false): ThemeName {
  const tema = validarTema(value);
  document.documentElement.dataset.theme = tema;
  if (persistir) {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, tema);
    } catch {
      /* Puede estar bloqueado. */
    }
  }
  return tema;
}
export function iniciarTema() {
  let preferencia: string | null = null;
  try {
    preferencia = localStorage.getItem(THEME_STORAGE_KEY);
  } catch {
    /* Usa el predeterminado. */
  }
  return aplicarTema(preferencia);
}
export function restablecerTema() {
  try {
    localStorage.removeItem(THEME_STORAGE_KEY);
  } catch {
    /* Sin almacenamiento persistente. */
  }
  return aplicarTema(DEFAULT_THEME);
}
