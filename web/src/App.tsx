import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Logo } from "./logo";
import { EventFilters } from "./components/EventFilters";
import { EventList } from "./components/EventList";
import { Hero } from "./components/Hero";
import { dateSortKey } from "./utils/date";
import type { EventsPayload } from "./types";

function App() {
  const { t } = useTranslation();
  const [payload, setPayload] = useState<EventsPayload | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [discipline, setDiscipline] = useState("all");

  useEffect(() => {
    let cancelled = false;

    fetch(`${import.meta.env.BASE_URL}events.json`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to load events (${response.status})`);
        }
        return response.json() as Promise<EventsPayload>;
      })
      .then((data) => {
        if (!cancelled) {
          setPayload(data);
          setLoadError(null);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setLoadError(error instanceof Error ? error.message : t("app.loadError"));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [t]);

  const disciplines = useMemo(() => {
    if (!payload) return [];
    const codes = new Set(payload.events.map((e) => e.discipline));
    return Array.from(codes);
  }, [payload]);

  const filteredEvents = useMemo(() => {
    if (!payload) return [];

    const query = search.trim().toLowerCase();

    return payload.events
      .filter((event) => {
        if (discipline !== "all" && event.discipline !== discipline) return false;
        if (!query) return true;

        const haystack = [
          event.title,
          event.description,
          event.source_name,
          event.location,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        return haystack.includes(query);
      })
      .sort((a, b) => dateSortKey(a.start_date) - dateSortKey(b.start_date));
  }, [payload, search, discipline]);

  if (loadError) {
    return (
      <div className="page">
        <div className="empty-state">
          <p>{t("app.loadError")}</p>
          <p className="empty-state__hint">{loadError}</p>
        </div>
      </div>
    );
  }

  if (!payload) {
    return (
      <div className="page">
        <div className="empty-state">
          <p>{t("app.loading")}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <Hero generatedAt={payload.generated_at} />

      <main className="main">
        <EventFilters
          search={search}
          discipline={discipline}
          disciplines={disciplines}
          resultCount={filteredEvents.length}
          onSearchChange={setSearch}
          onDisciplineChange={setDiscipline}
        />
        <EventList events={filteredEvents} />
      </main>

      <div className="footer-shell">
        <footer className="footer">
          <Logo variant="mark" size={40} className="footer__logo" title="Soscitea" />
          <div>
            <p className="footer__title">{t("footer.about")}</p>
            <p className="footer__text">{t("footer.text")}</p>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
