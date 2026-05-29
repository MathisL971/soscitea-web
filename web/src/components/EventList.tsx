import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { EventDayCarousel } from "./EventDayCarousel";
import { formatEventDate } from "../utils/date";
import type { Event } from "../types";

interface EventListProps {
  events: Event[];
}

export function EventList({ events }: EventListProps) {
  const { t, i18n } = useTranslation();

  const grouped = useMemo(
    () => groupByDate(events, i18n.language),
    [events, i18n.language],
  );

  if (events.length === 0) {
    return (
      <div className="empty-state">
        <p>{t("events.empty")}</p>
        <p className="empty-state__hint">{t("events.emptyHint")}</p>
      </div>
    );
  }

  return (
    <div className="event-list">
      {grouped.map(([dateLabel, dayEvents]) => (
        <section key={dateLabel} className="event-day">
          <h2 className="event-day__heading">{dateLabel}</h2>
          <EventDayCarousel dateLabel={dateLabel} events={dayEvents} />
        </section>
      ))}
    </div>
  );
}

function groupByDate(events: Event[], language: string): [string, Event[]][] {
  const map = new Map<string, Event[]>();

  for (const event of events) {
    const label = formatEventDate(event.start_date, language);
    const bucket = map.get(label);
    if (bucket) {
      bucket.push(event);
    } else {
      map.set(label, [event]);
    }
  }

  return Array.from(map.entries());
}
