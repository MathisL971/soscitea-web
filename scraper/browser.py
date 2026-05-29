from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_BROWSER = None
_PLAYWRIGHT = None


def fetch_html(url: str, *, wait_ms: int = 2000) -> str:
    """Fetch rendered HTML via headless Chromium (for bot-protected sites)."""
    global _BROWSER, _PLAYWRIGHT
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install chromium") from exc

    if _BROWSER is None:
        _PLAYWRIGHT = sync_playwright().start()
        _BROWSER = _PLAYWRIGHT.chromium.launch(headless=True)

    page = _BROWSER.new_page(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="fr-CA",
    )
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(wait_ms)
        return page.content()
    finally:
        page.close()


def close_browser() -> None:
    global _BROWSER, _PLAYWRIGHT
    if _BROWSER is not None:
        _BROWSER.close()
        _BROWSER = None
    if _PLAYWRIGHT is not None:
        _PLAYWRIGHT.stop()
        _PLAYWRIGHT = None
