import { useTranslation } from "react-i18next";
import { DISCIPLINE_ORDER, disciplineLabel, normalizeDisciplineCode } from "../disciplines";

interface EventFiltersProps {
  search: string;
  discipline: string;
  disciplines: string[];
  resultCount: number;
  onSearchChange: (value: string) => void;
  onDisciplineChange: (value: string) => void;
}

export function EventFilters({
  search,
  discipline,
  disciplines,
  resultCount,
  onSearchChange,
  onDisciplineChange,
}: EventFiltersProps) {
  const { t } = useTranslation();

  const sortedDisciplines = [...disciplines].sort((a, b) => {
    const indexA = DISCIPLINE_ORDER.indexOf(normalizeDisciplineCode(a));
    const indexB = DISCIPLINE_ORDER.indexOf(normalizeDisciplineCode(b));
    return (indexA === -1 ? DISCIPLINE_ORDER.length : indexA)
      - (indexB === -1 ? DISCIPLINE_ORDER.length : indexB);
  });

  return (
    <section className="filters" aria-label={t("filters.aria")}>
      <div className="section-heading">
        <h2 className="section-heading__title">{t("filters.title")}</h2>
        <p className="section-heading__subtitle">
          {t("filters.resultCount", { count: resultCount })}
        </p>
      </div>

      <div className="filters__row">
        <label className="search-field">
          <span className="search-field__label">{t("filters.search")}</span>
          <input
            type="search"
            placeholder={t("filters.searchPlaceholder")}
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </label>

        <label className="discipline-select">
          <span className="discipline-select__label">{t("filters.discipline")}</span>
          <select value={discipline} onChange={(e) => onDisciplineChange(e.target.value)}>
            <option value="all">{t("filters.allFields")}</option>
            {sortedDisciplines.map((code) => (
              <option key={code} value={code}>
                {disciplineLabel(code)}
              </option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}
