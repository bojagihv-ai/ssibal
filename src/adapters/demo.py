from __future__ import annotations

import hashlib
from pathlib import Path

from src.adapters.base import BaseAdapter
from src.core.models import DownloadResult, ListingCandidate, ListingMeta


class DemoAdapter(BaseAdapter):
    def __init__(self, name: str):
        self.name = name

    def search_by_image(self, image_path: str, query_hint: str, max_candidates: int) -> list[ListingCandidate]:
        q = query_hint or "sample-product"
        items = []
        for i in range(min(max_candidates, 5)):
            url = f"https://example.com/{self.name}/{q}/{i}"
            items.append(
                ListingCandidate(
                    platform=self.name,
                    item_id=hashlib.md5(url.encode()).hexdigest()[:12],
                    title=f"[{self.name}] {q} candidate {i}",
                    url=url,
                    image_url="https://picsum.photos/seed/demo/400/400",
                    price=10000 + i * 1000,
                    review_count=10 * (i + 1),
                    rating=4.0,
                    sales_metric=5 * (i + 1),
                )
            )
        return items

    def enrich_listing(self, listing_url: str) -> ListingMeta:
        return ListingMeta(price_min=10000, price_max=12000, review_count=10, rating=4.0, sales_metric=5)

    def crawl_detail_images(self, listing_url: str, save_dir: Path) -> DownloadResult:
        return DownloadResult(
            extracted_urls=["https://picsum.photos/seed/detail1/1200/1200"],
            downloaded_files=[],
            failed_urls=[],
        )
