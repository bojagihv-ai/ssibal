from __future__ import annotations

import hashlib
import time
from abc import ABC, abstractmethod
from typing import Any


class ShoppingProduct:
    __slots__ = (
        "item_id", "mall_id", "mall_name", "category_id", "category_name",
        "title", "url", "image_url", "price", "seller",
        "rating", "review_count", "crawled_at",
    )

    def __init__(self, **kw: Any) -> None:
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__slots__}

    @staticmethod
    def make_id(url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()[:16]


class BaseMallCrawler(ABC):
    mall_id: str
    mall_name: str
    rate_limit_s: float = 1.2

    def crawl(
        self,
        category_id: str,
        category_name: str,
        keywords: list[str],
        max_items: int = 30,
    ) -> list[ShoppingProduct]:
        results: list[ShoppingProduct] = []
        seen_urls: set[str] = set()

        for kw in keywords[:3]:
            time.sleep(self.rate_limit_s)
            try:
                found = self._search(kw, max_items)
                for p in found:
                    if p.url not in seen_urls:
                        seen_urls.add(p.url)
                        p.category_id = category_id
                        p.category_name = category_name
                        p.mall_id = self.mall_id
                        p.mall_name = self.mall_name
                        results.append(p)
            except Exception:
                pass
            if len(results) >= max_items:
                break

        return results[:max_items]

    @abstractmethod
    def _search(self, keyword: str, max_items: int) -> list[ShoppingProduct]:
        raise NotImplementedError
