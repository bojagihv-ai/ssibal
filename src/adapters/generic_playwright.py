from __future__ import annotations

from pathlib import Path

from src.core.models import DownloadResult
from src.core.storage import download_images, extract_image_urls_from_html


def crawl_with_playwright(listing_url: str, save_dir: Path) -> DownloadResult:
    from playwright.sync_api import sync_playwright

    save_dir.mkdir(parents=True, exist_ok=True)
    result = DownloadResult()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1800})
        page.goto(listing_url, wait_until="domcontentloaded", timeout=45000)
        for _ in range(12):
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(300)
        html = page.content()
        snapshot_path = save_dir / "page_snapshot.html"
        snapshot_path.write_text(html, encoding="utf-8")
        result.snapshot_html_path = str(snapshot_path)

        try:
            full_png = save_dir / "page_full.png"
            page.screenshot(path=str(full_png), full_page=True)
            result.fullpage_png_path = str(full_png)
        except Exception:
            pass
        browser.close()

    result.extracted_urls = extract_image_urls_from_html(html, listing_url)
    result.downloaded_files, result.failed_urls = download_images(result.extracted_urls, save_dir / "detail_images")
    return result
