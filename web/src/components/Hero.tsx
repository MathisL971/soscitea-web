import { useTranslation } from "react-i18next";
import { Logo } from "../logo";
import { LanguageToggle } from "./LanguageToggle";
import { ThemeToggle } from "./ThemeToggle";
import { formatEditionDate, formatRelativeUpdate } from "../utils/date";

interface HeroProps {
  generatedAt: string;
}

export function Hero({ generatedAt }: HeroProps) {
  const { t, i18n } = useTranslation();

  return (
    <header className="masthead">
      <div className="masthead__body">
        <div className="masthead__top">
          <div className="masthead__brand">
            <h1 className="masthead__title-lockup">
              <Logo variant="lockup" size={64} title="Soscitea" />
            </h1>
          </div>

          <aside className="masthead__edition" aria-label={t("hero.statusAria")}>
            <div className="masthead__edition-header">
              <div className="masthead__controls">
                <ThemeToggle />
                <LanguageToggle />
              </div>
            </div>
            <div className="masthead__edition-meta">
              <time className="masthead__edition-date" dateTime={generatedAt}>
                {formatEditionDate(generatedAt, i18n.language)}
              </time>
              <span className="masthead__edition-note">
                {formatRelativeUpdate(generatedAt, i18n.language)}
              </span>
            </div>
          </aside>
        </div>

        <p className="masthead__deck">{t("hero.deck")}</p>
      </div>
    </header>
  );
}
