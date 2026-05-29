import { useTranslation } from "react-i18next";
import { normalizeLanguage, type SupportedLanguage } from "../i18n";

export function LanguageToggle() {
  const { t, i18n } = useTranslation();
  const current = normalizeLanguage(i18n.language);

  function setLanguage(language: SupportedLanguage) {
    if (language !== current) {
      void i18n.changeLanguage(language);
    }
  }

  return (
    <div className="lang-toggle" role="group" aria-label={t("language.label")}>
      <button
        type="button"
        className={`lang-toggle__btn${current === "en" ? " lang-toggle__btn--active" : ""}`}
        aria-pressed={current === "en"}
        onClick={() => setLanguage("en")}
      >
        EN
      </button>
      <span className="lang-toggle__sep" aria-hidden="true">
        /
      </span>
      <button
        type="button"
        className={`lang-toggle__btn${current === "fr" ? " lang-toggle__btn--active" : ""}`}
        aria-pressed={current === "fr"}
        onClick={() => setLanguage("fr")}
      >
        FR
      </button>
    </div>
  );
}
