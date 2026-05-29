import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { EventCard } from "./EventCard";
import type { Event } from "../types";

interface EventDayCarouselProps {
  dateLabel: string;
  events: Event[];
}

function CarouselArrow({ direction }: { direction: "prev" | "next" }) {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
      {direction === "prev" ? (
        <path
          d="M15 6l-6 6 6 6"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ) : (
        <path
          d="M9 6l6 6-6 6"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
    </svg>
  );
}

export function EventDayCarousel({ dateLabel, events }: EventDayCarouselProps) {
  const { t } = useTranslation();
  const trackRef = useRef<HTMLDivElement>(null);
  const [canPrev, setCanPrev] = useState(false);
  const [canNext, setCanNext] = useState(false);

  const updateScrollState = useCallback(() => {
    const el = trackRef.current;
    if (!el) return;

    const { scrollLeft, scrollWidth, clientWidth } = el;
    setCanPrev(scrollLeft > 4);
    setCanNext(scrollLeft + clientWidth < scrollWidth - 4);
  }, []);

  useEffect(() => {
    const el = trackRef.current;
    if (!el) return;

    updateScrollState();

    el.addEventListener("scroll", updateScrollState, { passive: true });
    const observer = new ResizeObserver(updateScrollState);
    observer.observe(el);

    return () => {
      el.removeEventListener("scroll", updateScrollState);
      observer.disconnect();
    };
  }, [updateScrollState, events]);

  const scroll = (direction: -1 | 1) => {
    const el = trackRef.current;
    if (!el) return;

    const card = el.querySelector<HTMLElement>(".event-card");
    const gap = Number.parseFloat(getComputedStyle(el).gap) || 14;
    const step = card ? card.offsetWidth + gap : el.clientWidth * 0.85;

    el.scrollBy({
      left: direction * step,
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "auto"
        : "smooth",
    });
  };

  return (
    <div className="event-day__carousel-shell">
      <div
        ref={trackRef}
        className="event-day__carousel"
        tabIndex={0}
        aria-label={t("events.dayCarousel", { date: dateLabel })}
      >
        {events.map((event) => (
          <EventCard key={event.id} event={event} />
        ))}
      </div>

      {canPrev && (
        <>
          <div className="event-day__carousel-fade event-day__carousel-fade--start" aria-hidden="true" />
          <button
            type="button"
            className="event-day__carousel-arrow event-day__carousel-arrow--prev"
            aria-label={t("events.carouselPrev")}
            onClick={() => scroll(-1)}
          >
            <CarouselArrow direction="prev" />
          </button>
        </>
      )}

      {canNext && (
        <>
          <div className="event-day__carousel-fade event-day__carousel-fade--end" aria-hidden="true" />
          <button
            type="button"
            className="event-day__carousel-arrow event-day__carousel-arrow--next"
            aria-label={t("events.carouselNext")}
            onClick={() => scroll(1)}
          >
            <CarouselArrow direction="next" />
          </button>
        </>
      )}
    </div>
  );
}
