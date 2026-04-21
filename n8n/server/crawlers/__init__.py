from .base import BaseMallCrawler, ShoppingProduct
from .coupang import CoupangCrawler
from .gmarket import ElevenstCrawler, GmarketCrawler, LotteonCrawler, SsgCrawler
from .naver import NaverShoppingCrawler

CRAWLERS: dict[str, type[BaseMallCrawler]] = {
    "coupang":  CoupangCrawler,
    "naver":    NaverShoppingCrawler,
    "gmarket":  GmarketCrawler,
    "elevenst": ElevenstCrawler,
    "ssg":      SsgCrawler,
    "lotteon":  LotteonCrawler,
}

__all__ = [
    "BaseMallCrawler", "ShoppingProduct", "CRAWLERS",
    "CoupangCrawler", "NaverShoppingCrawler",
    "GmarketCrawler", "ElevenstCrawler", "SsgCrawler", "LotteonCrawler",
]
