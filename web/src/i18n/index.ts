import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";
import fr from "./locales/fr.json";

export const supportedLanguages = ["en", "fr"] as const;
export type SupportedLanguage = (typeof supportedLanguages)[number];

export function normalizeLanguage(language: string | undefined): SupportedLanguage {
  return language?.startsWith("fr") ? "fr" : "en";
}

export function localeTag(language: string | undefined): "en-CA" | "fr-CA" {
  return normalizeLanguage(language) === "fr" ? "fr-CA" : "en-CA";
}

function syncDocumentMeta(language: string) {
  document.documentElement.lang = normalizeLanguage(language);
  document.title = i18n.t("meta.title");

  const description = document.querySelector('meta[name="description"]');
  if (description) {
    description.setAttribute("content", i18n.t("meta.description"));
  }
}

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      fr: { translation: fr },
    },
    fallbackLng: "en",
    supportedLngs: ["en", "fr"],
    nonExplicitSupportedLngs: true,
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ["localStorage", "navigator"],
      caches: ["localStorage"],
      lookupLocalStorage: "soscitea-lang",
    },
  })
  .then(() => {
    syncDocumentMeta(i18n.language);
  });

i18n.on("languageChanged", syncDocumentMeta);

export default i18n;
