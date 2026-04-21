from __future__ import annotations

import json
import re
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
    "Referer": "https://search.shopping.naver.com/",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


class NaverShoppingCrawler(BaseMallCrawler):
    mall_id = "naver"
    mall_name = "네이버쇼핑"

    def _search(self, keyword: str, max_items: int) -> list[ShoppingProduct]:
        url = (
            f"https://search.shopping.naver.com/search/all"
            f"?query={quote(keyword)}&pagingSize={min(max_items, 40)}"
        )
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=20)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results: list[ShoppingProduct] = []
        now = datetime.utcnow().isoformat()

        # 네이버쇼핑은 __NEXT_DATA__ JSON에서 데이터 추출
        script = soup.find("script", id="__NEXT_DATA__")
        if script:
            try:
                data = json.loads(script.string)
                items = (
                    data.get("props", {})
                    .get("pageProps", {})
                    .get("initialState", {})
                    .get("products", {})
                    .get("list", [])
                )
                for item in items[:max_items]:
                    p = item.get("item", item)
                    listing_url = p.get("mallProductUrl") or p.get("crUrl") or ""
                    if not listing_url:
                        continue
                    price_raw = p.get("lprice") or p.get("price") or 0
                    try:
                        price = float(str(price_raw).replace(",", ""))
                    except ValueError:
                        price = None
                    results.append(ShoppingProduct(
                        item_id=ShoppingProduct.make_id(listing_url),
                        title=(p.get("productTitle") or p.get("title") or "")[:200],
                        url=listing_url,
                        image_url=p.get("imageUrl") or p.get("img") or "",
                        price=price,
                        seller=p.get("mallName") or p.get("maker") or "",
                        rating=None,
                        review_count=int(p.get("reviewCount") or 0),
                        crawled_at=now,
                    ))
                return results
            except Exception:
                pass

        # fallback: HTML 파싱
        for el in soup.select("div.basicList_item__0T9JD, li[class*='product']")[:max_items]:
            a = el.find("a", href=True)
            if not a:
                continue
            href = a["href"]
            if not href.startswith("http"):
                href = "https://search.shopping.naver.com" + href
            title_el = el.select_one("a[class*='title'], div[class*='title']")
            title = title_el.get_text(strip=True)[:200] if title_el else a.get_text(strip=True)[:200]
            if not title:
                continue
            price_el = el.select_one("span[class*='price'], em[class*='price']")
            price = None
            if price_el:
                m = re.search(r"[\d,]+", price_el.get_text())
                if m:
                    try:
                        price = float(m.group().replace(",", ""))
                    except ValueError:
                        pass
            img = el.find("img")
            image_url = (img.get("src") or img.get("data-src") or "") if img else ""
            results.append(ShoppingProduct(
                item_id=ShoppingProduct.make_id(href),
                title=title,
                url=href,
                image_url=image_url,
                price=price,
                crawled_at=now,
            ))

        return results
