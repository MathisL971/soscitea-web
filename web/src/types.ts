export interface Event {
  id: string;
  title: string;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
  location: string | null;
  url: string | null;
  source_url: string;
  source_name: string;
  discipline: string;
  status: string;
  scraped_at: string;
  first_seen_at?: string;
  last_seen_at?: string;
}

export interface EventsPayload {
  generated_at: string;
  region: string;
  topic: string;
  event_count: number;
  sources_ok: number | null;
  sources_failed: number | null;
  events: Event[];
}
