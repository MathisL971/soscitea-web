import i18n from "./i18n";

export const DISCIPLINE_COLORS: Record<string, string> = {
  polisci: "#3d5a80",
  philo: "#6b4c7a",
  econ: "#2d6a4f",
  socio: "#9c4221",
  anthrop: "#8b6914",
  psych: "#7b4966",
  hist: "#6c584c",
  relig: "#5c4d7d",
  general: "#7c6a5a",
};

const DISCIPLINE_ALIASES: Record<string, string> = {
  history: "hist",
};

export function normalizeDisciplineCode(code: string): string {
  return DISCIPLINE_ALIASES[code] ?? code;
}

export function disciplineLabel(code: string): string {
  return i18n.t(`disciplines.${normalizeDisciplineCode(code)}`, { defaultValue: code });
}

export function disciplineColor(code: string): string {
  const key = normalizeDisciplineCode(code);
  return DISCIPLINE_COLORS[key] ?? DISCIPLINE_COLORS.general;
}

export const DISCIPLINE_ORDER = [
  "polisci",
  "philo",
  "econ",
  "socio",
  "anthrop",
  "psych",
  "hist",
  "relig",
  "general",
];
