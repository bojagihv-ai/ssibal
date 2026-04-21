from __future__ import annotations

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
    "Accept-Language": "ko-KR,ko;q=0.9",
}


class GmarketCrawler(BaseMallCrawler):
    mall_id = "gmarket"
    mall_name = "G마켓"

    def _search(self, keyword: str, max_items: int) -> list[ShoppingProduct]:
        url = f"https://browse.gmarket.co.kr/search?keyword={quote(keyword)}&pageSize={min(max_items, 40)}"
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=20)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results: list[ShoppingProduct] = []
        now = datetime.utcnow().isoformat()

        for card in soup.select("li.item__item, div.list-item")[:max_items]:
            a = card.select_one("a.itemname, a.item__name, a[href*='item.gmarket']")
            if not a:
                a = card.find("a", href=re.compile(r"item\.gmarket|gmarket\.co\.kr"))
            if not a:
                continue
            href = a.get("href", "")
            if not href.startswith("http"):
                href = "https:" + href if href.startswith("//") else f"https://browse.gmarket.co.kr{href}"
            title = a.get_text(strip=True)[:200]
            if not title:
                continue

            price_el = card.select_one("span.price__value, strong.price, span.buy-price")
            price = None
            if price_el:
                m = re.search(r"[\d,]+", price_el.get_text())
                if m:
                    try:
                        price = float(m.group().replace(",", ""))
                    except ValueError:
                        pass

            img = card.find("img")
            image_url = ""
            if img:
                image_url = img.get("src") or img.get("data-src") or ""
                if image_url.startswith("//"):
                    image_url = "https:" + image_url

            results.append(ShoppingProduct(
                item_id=ShoppingProduct.make_id(href),
                title=title,
                url=href,
                image_url=image_url,
                price=price,
                crawled_at=now,
            ))

        return results


class ElevenstCrawler(BaseMallCrawler):
    mall_id = "11st"
    mall_name = "11번가"

    def _search(self, keyword: str, max_items: int) -> list[ShoppingProduct]:
        url = (
            f"https://search.11st.co.kr/Search.tmall"
            f"?kwd={quote(keyword)}&pageSize={min(max_items, 40)}"
        )
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=20)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results: list[ShoppingProduct] = []
        now = datetime.utcnow().isoformat()

        for card in soup.select("li.prd-item, div.c-prd-item")[:max_items]:
            a = card.select_one("a.prd-name, a[href*='11st.co.kr']")
            if not a:
                a = card.find("a", href=re.compile(r"11st\.co\.kr"))
            if not a:
                continue
            href = a.get("href", "")
            if not href.startswith("http"):
                href = "https:" + href if href.startswith("//") else f"https://search.11st.co.kr{href}"
            title = a.get_text(strip=True)[:200]
            if not title:
                title_el = card.select_one("span.prd-name, div.prd-name")
                title = title_el.get_text(strip=True)[:200] if title_el else ""
            if not title:
                continue

            price_el = card.select_one("span.price-value, em.price, span.sale-price")
            price = None
            if price_el:
                m = re.search(r"[\d,]+", price_el.get_text())
                if m:
                    try:
                        price = float(m.group().replace(",", ""))
                    except ValueError:
                        pass

            img = card.find("img")
            image_url = ""
            if img:
                image_url = img.get("src") or img.get("data-src") or ""
                if image_url.startswith("//"):
                    image_url = "https:" + image_url

            results.append(ShoppingProduct(
                item_id=ShoppingProduct.make_id(href),
                title=title,
                url=href,
                image_url=image_url,
                price=price,
                crawled_at=now,
            ))

        return results


class SsgCrawler(BaseMallCrawler):
    mall_id = "ssg"
    mall_name = "SSG닷컴"

    def _search(self, keyword: str, max_items: int) -> list[ShoppingProduct]:
        url = f"https://www.ssg.com/search.ssg?target=all&query={quote(keyword)}&pageSize={min(max_items, 40)}"
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=20)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results: list[ShoppingProduct] = []
        now = datetime.utcnow().isoformat()

        for card in soup.select("li.cunit_t, li.cunit_ty2")[:max_items]:
            a = card.select_one("a.cunit_info, a[href*='ssg.com/item']")
            if not a:
                a = card.find("a", href=re.compile(r"ssg\.com/item"))
            if not a:
                continue
            href = a.get("href", "")
            if not href.startswith("http"):
                href = "https://www.ssg.com" + href
            title_el = card.select_one("span.cunit_name, div.cunit_name")
            title = title_el.get_text(strip=True)[:200] if title_el else a.get_text(strip=True)[:200]
            if not title:
                continue

            price_el = card.select_one("em.ssg_price, span.sale_price")
            price = None
            if price_el:
                m = re.search(r"[\d,]+", price_el.get_text())
                if m:
                    try:
                        price = float(m.group().replace(",", ""))
                    except ValueError:
                        pass

            img = card.find("img")
            image_url = ""
            if img:
                image_url = img.get("src") or img.get("data-src") or ""
                if image_url.startswith("//"):
                    image_url = "https:" + image_url

            results.append(ShoppingProduct(
                item_id=ShoppingProduct.make_id(href),
                title=title,
                url=href,
                image_url=image_url,
                price=price,
                crawled_at=now,
            ))

        return results


class LotteonCrawler(BaseMallCrawler):
    mall_id = "lotteon"
    mall_name = "롯데온"

    def _search(self, keyword: str, max_items: int) -> list[ShoppingProduct]:
        url = f"https://www.lotteon.com/search/search?query={quote(keyword)}&rowsPerPage={min(max_items, 40)}"
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=20)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results: list[ShoppingProduct] = []
        now = datetime.utcnow().isoformat()

        for card in soup.select("li.prod-item, div.search_item")[:max_items]:
            a = card.find("a", href=re.compile(r"lotteon\.com"))
            if not a:
                a = card.find("a", href=True)
            if not a:
                continue
            href = a.get("href", "")
            if not href.startswith("http"):
                href = "https://www.lotteon.com" + href
            title_el = card.select_one("strong.prod-name, span.prod_name")
            title = title_el.get_text(strip=True)[:200] if title_el else a.get_text(strip=True)[:200]
            if not title:
                continue

            price_el = card.select_one("strong.price, span.sale-price")
            price = None
            if price_el:
                m = re.search(r"[\d,]+", price_el.get_text())
                if m:
                    try:
                        price = float(m.group().replace(",", ""))
                    except ValueError:
                        pass

            img = card.find("img")
            image_url = ""
            if img:
                image_url = img.get("src") or img.get("data-src") or ""
                if image_url.startswith("//"):
                    image_url = "https:" + image_url

            results.append(ShoppingProduct(
                item_id=ShoppingProduct.make_id(href),
                title=title,
                url=href,
                image_url=image_url,
                price=price,
                crawled_at=now,
            ))

        return results
