from __future__ import annotations

import httpx
import certifi

try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 45.0


def create_client() -> httpx.Client:
    return httpx.Client(
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-CA,fr;q=0.9,en-CA,en;q=0.8",
            "Referer": "https://www.google.com/",
        },
        timeout=DEFAULT_TIMEOUT,
        follow_redirects=True,
        verify=certifi.where(),
    )


def fetch_text(client: httpx.Client, url: str, *, browser_fallback: bool = False) -> str:
    try:
        response = client.get(url)
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as exc:
        if browser_fallback and exc.response.status_code in {403, 429, 503}:
            from scraper.browser import fetch_html

            return fetch_html(url)
        raise
