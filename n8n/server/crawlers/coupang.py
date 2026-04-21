from __future__ import annotations

from datetime import datetime
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from .base import BaseMallCrawler, ShoppingProduct

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


class CoupangCrawler(BaseMallCrawler):
    mall_id = "coupang"
    mall_name = "쿠팡"

    def _search(self, keyword: str, max_items: int) -> list[ShoppingProduct]:
        url = f"https://www.coupang.com/np/search?q={quote(keyword)}&listSize={max_items}"
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=20)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results: list[ShoppingProduct] = []
        now = datetime.utcnow().isoformat()

        for card in soup.select("li.search-product")[:max_items]:
            a = card.select_one("a.search-product-link")
            if not a:
                continue
            href = a.get("href", "")
            listing_url = href if href.startswith("http") else f"https://www.coupang.com{href}"

            title_el = card.select_one("div.name")
            title = title_el.get_text(strip=True)[:200] if title_el else ""
            if not title:
                continue

            img = card.select_one("img")
            image_url = ""
            if img:
                image_url = img.get("src") or img.get("data-img-src") or ""

            price_el = card.select_one("em.price-value")
            price: float | None = None
            if price_el:
                try:
                    price = float(price_el.get_text(strip=True).replace(",", ""))
                except ValueError:
                    pass

            rating_el = card.select_one("em.rating")
            rating: float | None = None
            if rating_el:
                try:
                    rating = float(rating_el.get_text(strip=True))
                except ValueError:
                    pass

            review_el = card.select_one("span.rating-total-count")
            review_count = 0
            if review_el:
                try:
                    review_count = int(
                        review_el.get_text(strip=True).strip("()").replace(",", "")
                    )
                except ValueError:
                    pass

            results.append(ShoppingProduct(
                item_id=ShoppingProduct.make_id(listing_url),
                title=title,
                url=listing_url,
                image_url=image_url,
                price=price,
                rating=rating,
                review_count=review_count,
                crawled_at=now,
            ))

        return results
