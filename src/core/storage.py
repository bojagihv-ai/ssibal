from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

from src.core.models import DownloadResult

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def normalize_url(base_url: str, raw: str) -> str:
    value = (raw or "").strip().strip('"').strip("'")
    if not value:
        return ""
    if value.startswith("//"):
        return f"https:{value}"
    return urljoin(base_url, value)


def safe_filename_from_url(url: str, idx: int) -> str:
    parsed = urlparse(url)
    tail = Path(parsed.path).suffix.lower()
    ext = tail if tail in IMG_EXT else ".jpg"
    digest = hashlib.md5(url.encode("utf-8")).hexdigest()[:12]
    return f"img_{idx:04d}_{digest}{ext}"


def download_images(urls: list[str], save_dir: Path, session=None, retries: int = 2, backoff_s: float = 0.8) -> tuple[list[str], list[str]]:
    import requests

    save_dir.mkdir(parents=True, exist_ok=True)
    s = session or requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 sachyo/0.2"})
    downloaded, failed = [], []
    for i, url in enumerate(urls, start=1):
        ok = False
        for attempt in range(retries + 1):
            try:
                r = s.get(url, timeout=20)
                r.raise_for_status()
                path = save_dir / safe_filename_from_url(url, i)
                path.write_bytes(r.content)
                downloaded.append(str(path))
                ok = True
                break
            except Exception:
                if attempt < retries:
                    time.sleep(backoff_s * (attempt + 1))
        if not ok:
            failed.append(url)
    return downloaded, failed


def extract_image_urls_from_html(html: str, base_url: str) -> list[str]:
    urls: set[str] = set()
    patterns = [
        r'src=["\']([^"\']+)["\']',
        r'data-src=["\']([^"\']+)["\']',
        r'srcset=["\']([^"\']+)["\']',
        r'background-image:\s*url\(["\']?([^"\')]+)',
    ]
    for pat in patterns:
        for m in re.finditer(pat, html, flags=re.IGNORECASE):
            raw = m.group(1).split(",")[0].strip().split(" ")[0]
            url = normalize_url(base_url, raw)
            if url.startswith("http"):
                urls.add(url)
    for m in re.finditer(r'https?://[^"\'\s>]+\.(?:jpg|jpeg|png|webp|gif|bmp)', html, flags=re.IGNORECASE):
        urls.add(m.group(0))
    return sorted(urls)


def write_run_config(path: Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def save_download_manifest(path: Path, result: DownloadResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "extracted_count": len(result.extracted_urls),
                "downloaded_count": len(result.downloaded_files),
                "failed_count": len(result.failed_urls),
                "failed_urls": result.failed_urls,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
