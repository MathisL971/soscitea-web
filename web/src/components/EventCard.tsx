import type { CSSProperties } from "react";
import { useTranslation } from "react-i18next";
import { disciplineColor, disciplineLabel } from "../disciplines";
import { formatEventDate, formatEventTime, truncate } from "../utils/date";
import type { Event } from "../types";

interface EventCardProps {
  event: Event;
}

export function EventCard({ event }: EventCardProps) {
  const { i18n } = useTranslation();
  const time = formatEventTime(event.start_date, i18n.language);
  const description = event.description
    ? truncate(event.description.replace(/\s+/g, " "), 160)
    : null;
  const accent = disciplineColor(event.discipline);

  return (
    <article
      className="event-card"
      style={{ "--discipline-accent": accent } as CSSProperties}
    >
      <div className="event-card__spine" aria-hidden="true" />

      <div className="event-card__body">
        <div className="event-card__meta">
          <span className="discipline-tag">{disciplineLabel(event.discipline)}</span>
          <span className="event-card__source">{event.source_name}</span>
        </div>

        <h3 className="event-card__title">
          {event.url ? (
            <a href={event.url} target="_blank" rel="noopener noreferrer">
              {event.title}
            </a>
          ) : (
            event.title
          )}
        </h3>

        <div className="event-card__when">
          <time dateTime={event.start_date ?? undefined} className="event-card__datetime">
            {formatEventDate(event.start_date, i18n.language)}
            {time ? ` · ${time}` : ""}
          </time>
          {event.location && <span className="event-card__location">{event.location}</span>}
        </div>

        {description && <p className="event-card__description">{description}</p>}
      </div>
    </article>
  );
}
