from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ListingCandidate:
    platform: str
    item_id: str
    title: str
    url: str
    image_url: str = ""
    seller: str = ""
    price: float | None = None
    review_count: int | None = None
    rating: float | None = None
    sales_metric: float | None = None
    views_estimated: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    similarity_score: float = 0.0
    class_label: str = "unclassified"
    reason: str = ""

    verified_flag: bool = False
    confidence: float = 0.0
    fail_reasons: str = ""
    compare_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["raw"] = str(self.raw)
        return data


@dataclass
class ListingMeta:
    price_min: float | None = None
    price_max: float | None = None
    shipping_fee: float | None = None
    option_text: str = ""
    review_count: int | None = None
    rating: float | None = None
    sales_metric: float | None = None
    category: str = ""


@dataclass
class DownloadResult:
    extracted_urls: list[str] = field(default_factory=list)
    downloaded_files: list[str] = field(default_factory=list)
    failed_urls: list[str] = field(default_factory=list)
    snapshot_html_path: str = ""
    fullpage_png_path: str = ""


@dataclass
class VerifyResult:
    verified_flag: bool
    confidence: float
    fail_reasons: list[str]
    compare_summary: str
