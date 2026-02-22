from __future__ import annotations

import hashlib
import time
from pathlib import Path
from urllib.parse import quote

from src.adapters.base import BaseAdapter
from src.adapters.generic_playwright import crawl_with_playwright
from src.core.models import DownloadResult, ListingCandidate, ListingMeta


class CoupangAdapter(BaseAdapter):
    name = "coupang"

    def __init__(self, rate_limit_s: float = 1.0):
        self.rate_limit_s = rate_limit_s

    def search_by_image(self, image_path: str, query_hint: str, max_candidates: int) -> list[ListingCandidate]:
        import requests
        from bs4 import BeautifulSoup

        if not query_hint.strip():
            return []
        time.sleep(self.rate_limit_s)
        q = quote(query_hint)
        url = f"https://www.coupang.com/np/search?q={q}"
        headers = {"User-Agent": "Mozilla/5.0 sachyo/0.2"}
        candidates: list[ListingCandidate] = []
        try:
            html = requests.get(url, headers=headers, timeout=20).text
            soup = BeautifulSoup(html, "lxml")
            cards = soup.select("li.search-product")[:max_candidates]
            for c in cards:
                a = c.select_one("a.search-product-link")
                if not a:
                    continue
                href = a.get("href", "")
                listing_url = href if href.startswith("http") else f"https://www.coupang.com{href}"
                title = (c.select_one("div.name") or c).get_text(strip=True)[:180]
                img = c.select_one("img")
                image_url = (img.get("src") or img.get("data-img-src") or "") if img else ""
                pid = hashlib.md5(listing_url.encode()).hexdigest()[:12]
                candidates.append(
                    ListingCandidate(platform=self.name, item_id=pid, title=title, url=listing_url, image_url=image_url)
                )
        except Exception:
            return []
        return candidates

    def enrich_listing(self, listing_url: str) -> ListingMeta:
        return ListingMeta()

    def crawl_detail_images(self, listing_url: str, save_dir: Path) -> DownloadResult:
        return crawl_with_playwright(listing_url, save_dir)
