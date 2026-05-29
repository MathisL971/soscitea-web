import { useTranslation } from "react-i18next";
import { useTheme } from "../hooks/useTheme";

export function ThemeToggle() {
  const { t } = useTranslation();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggleTheme}
      aria-pressed={isDark}
      aria-label={isDark ? t("theme.switchToLight") : t("theme.switchToDark")}
      title={isDark ? t("theme.light") : t("theme.dark")}
    >
      <span className="theme-toggle__icon" aria-hidden="true">
        {isDark ? (
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none">
            <circle cx="12" cy="12" r="4.25" stroke="currentColor" strokeWidth="1.75" />
            <path
              d="M12 2.25v2.1M12 19.65v2.1M4.35 12H2.25M21.75 12h-2.1M5.64 5.64l-1.49-1.49M19.85 19.85l-1.49-1.49M5.64 18.36l-1.49 1.49M19.85 4.15l-1.49 1.49"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
            />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none">
            <path
              d="M20.5 14.5a8.25 8.25 0 0 1-11-11 8.25 8.25 0 1 0 11 11Z"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </span>
      <span className="theme-toggle__label">{isDark ? t("theme.light") : t("theme.dark")}</span>
    </button>
  );
}
