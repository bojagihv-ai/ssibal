from __future__ import annotations

import hashlib
import time
from pathlib import Path
from urllib.parse import quote

from src.adapters.base import BaseAdapter
from src.adapters.generic_playwright import crawl_with_playwright
from src.core.models import DownloadResult, ListingCandidate, ListingMeta


class NaverSmartstoreAdapter(BaseAdapter):
    name = "naver"

    def __init__(self, rate_limit_s: float = 1.0):
        self.rate_limit_s = rate_limit_s

    def search_by_image(self, image_path: str, query_hint: str, max_candidates: int) -> list[ListingCandidate]:
        import requests
        from bs4 import BeautifulSoup

        if not query_hint.strip():
            return []
        time.sleep(self.rate_limit_s)
        q = quote(query_hint)
        url = f"https://search.shopping.naver.com/search/all?query={q}"
        headers = {"User-Agent": "Mozilla/5.0 sachyo/0.2"}
        out: list[ListingCandidate] = []
        try:
            html = requests.get(url, headers=headers, timeout=20).text
            soup = BeautifulSoup(html, "lxml")
            links = soup.select("a")
            for a in links:
                href = a.get("href", "")
                text = a.get_text(strip=True)
                if not href.startswith("http") or not text:
                    continue
                if "shopping" not in href and "smartstore" not in href:
                    continue
                pid = hashlib.md5(href.encode()).hexdigest()[:12]
                out.append(ListingCandidate(platform=self.name, item_id=pid, title=text[:180], url=href))
                if len(out) >= max_candidates:
                    break
        except Exception:
            return []
        return out

    def enrich_listing(self, listing_url: str) -> ListingMeta:
        return ListingMeta()

    def crawl_detail_images(self, listing_url: str, save_dir: Path) -> DownloadResult:
        return crawl_with_playwright(listing_url, save_dir)
