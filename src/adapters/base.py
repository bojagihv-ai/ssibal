from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.core.models import DownloadResult, ListingCandidate, ListingMeta


class BaseAdapter(ABC):
    name: str

    @abstractmethod
    def search_by_image(self, image_path: str, query_hint: str, max_candidates: int) -> list[ListingCandidate]:
        raise NotImplementedError

    @abstractmethod
    def enrich_listing(self, listing_url: str) -> ListingMeta:
        raise NotImplementedError

    @abstractmethod
    def crawl_detail_images(self, listing_url: str, save_dir: Path) -> DownloadResult:
        raise NotImplementedError
