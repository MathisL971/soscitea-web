"""One-off probe for Batch A source HTML structure."""
from __future__ import annotations

import httpx

from scraper.http import fetch_text

URLS = [
    ("CRE", "https://www.lecre.umontreal.ca/calendrier/"),
    ("CRISES", "https://crises.uqam.ca/activites/evenements-a-venir/"),
    ("CEIM", "https://www.ceim.uqam.ca/db/spip.php?rubrique27="),
    ("CELAT", "https://celat.ca/uqam/activites-uqam/"),
    ("BellesHeures", "https://bellesheures.umontreal.ca/themes-activites/societe/"),
    ("ENAP", "https://enap.ca/evenements"),
    ("CIRANO", "https://cirano.qc.ca/index.php/fr/list/evenements"),
    ("CIREQ", "https://cireqmontreal.com/en/"),
    ("UQAM_API", "https://evenements.uqam.ca/api/evenements?limit=3"),
]

def main() -> None:
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        for name, url in URLS:
            print(f"=== {name} ===")
            try:
                if name == "UQAM_API":
                    r = client.get(url)
                    print(r.status_code, r.text[:800])
                else:
                    html = fetch_text(client, url)
                    print(f"bytes={len(html)}")
                    for marker in ("tribe-events", "views-row", "article", "event-item", "spip", "h3"):
                        cnt = html.lower().count(marker)
                        if cnt:
                            print(f"  {marker}: {cnt}")
            except Exception as exc:
                print(f"FAILED: {exc}")
            print()

if __name__ == "__main__":
    main()
