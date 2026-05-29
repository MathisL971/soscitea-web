import i18n from "../i18n";
import { localeTag } from "../i18n";

const MONTREAL_TZ = "America/Montreal";

export function formatEventDate(iso: string | null, language = i18n.language): string {
  if (!iso) return i18n.t("events.dateTbd");

  const date = new Date(iso);
  return new Intl.DateTimeFormat(localeTag(language), {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: MONTREAL_TZ,
  }).format(date);
}

export function formatEventTime(iso: string | null, language = i18n.language): string | null {
  if (!iso) return null;

  const date = new Date(iso);
  const hours = date.getUTCHours();
  const minutes = date.getUTCMinutes();
  const locale = localeTag(language);

  // Midnight-only timestamps usually mean "date known, time unknown"
  if (hours === 4 && minutes === 0) {
    const localHours = new Date(iso).toLocaleString(locale, {
      hour: "numeric",
      minute: "2-digit",
      timeZone: MONTREAL_TZ,
      hour12: true,
    });
    if (localHours.startsWith("12:00")) return null;
  }

  return new Intl.DateTimeFormat(locale, {
    hour: "numeric",
    minute: "2-digit",
    timeZone: MONTREAL_TZ,
    hour12: true,
  }).format(date);
}

export function formatRelativeUpdate(iso: string, language = i18n.language): string {
  const updated = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - updated.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

  if (diffHours < 1) return i18n.t("date.updatedJustNow", { lng: language });
  if (diffHours < 24) {
    return i18n.t("date.updatedHoursAgo", { hours: diffHours, lng: language });
  }

  return new Intl.DateTimeFormat(localeTag(language), {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: MONTREAL_TZ,
  }).format(updated);
}

export function formatEditionDate(iso: string, language = i18n.language): string {
  return new Intl.DateTimeFormat(localeTag(language), {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: MONTREAL_TZ,
  }).format(new Date(iso));
}

export function dateSortKey(iso: string | null): number {
  if (!iso) return Number.MAX_SAFE_INTEGER;
  return new Date(iso).getTime();
}

export function truncate(text: string, max: number): string {
  if (text.length <= max) return text;
  return `${text.slice(0, max).trimEnd()}…`;
}
