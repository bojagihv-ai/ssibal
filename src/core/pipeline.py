from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path

from src.adapters.coupang import CoupangAdapter
from src.adapters.demo import DemoAdapter
from src.adapters.naver_smartstore import NaverSmartstoreAdapter
from src.core.models import ListingCandidate
from src.core.report import write_manual_review_html, write_reports
from src.core.similarity import score_candidates
from src.core.storage import save_download_manifest, write_run_config
from src.core.verify import verify_candidate


def build_adapters(sources: list[str]):
    adapter_map = {
        "coupang": CoupangAdapter,
        "naver": NaverSmartstoreAdapter,
    }
    adapters = []
    for src in sources:
        cls = adapter_map.get(src)
        adapters.append(cls() if cls else DemoAdapter(src))
    return adapters


def make_run_id(image_path: str, query_hint: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    h = hashlib.md5(f"{image_path}|{query_hint}|{ts}".encode()).hexdigest()[:8]
    return f"{ts}_{h}"


def run_pipeline(
    image_path: str,
    query_hint: str,
    max_candidates_per_source: int,
    topk_final: int,
    sources: list[str],
    output_base_dir: str,
    export_xlsx: bool = False,
    manual_review_topn: int = 30,
) -> dict:
    run_id = make_run_id(image_path, query_hint)
    output_dir = Path(output_base_dir) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler(output_dir / "run.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        format="%(asctime)s %(levelname)s %(message)s",
    )

    write_run_config(
        output_dir / "run_config.json",
        {
            "image": image_path,
            "query_hint": query_hint,
            "max_candidates_per_source": max_candidates_per_source,
            "topk_final": topk_final,
            "sources": sources,
            "manual_review_topn": manual_review_topn,
        },
    )

    adapters = build_adapters(sources)
    candidates: list[ListingCandidate] = []

    for adapter in adapters:
        try:
            found = adapter.search_by_image(image_path, query_hint, max_candidates_per_source)
            logging.info("source=%s candidates=%s", adapter.name, len(found))
            candidates.extend(found)
        except Exception as e:
            logging.exception("source=%s search_failed=%s", adapter.name, e)

    candidates = score_candidates(image_path, candidates, query_hint)[:topk_final]

    for c in candidates:
        vr = verify_candidate(c, query_hint)
        c.verified_flag = vr.verified_flag
        c.confidence = vr.confidence
        c.fail_reasons = " | ".join(vr.fail_reasons)
        c.compare_summary = vr.compare_summary

    for c in candidates:
        asset_dir = output_dir / "assets" / c.platform / c.item_id
        try:
            asset_dir.mkdir(parents=True, exist_ok=True)
            adapter = next(a for a in adapters if a.name == c.platform)
            result = adapter.crawl_detail_images(c.url, asset_dir)
            save_download_manifest(asset_dir / "download_manifest.json", result)
        except Exception as e:
            logging.exception("crawl_failed platform=%s url=%s err=%s", c.platform, c.url, e)

    write_reports(candidates, output_dir, export_xlsx=export_xlsx)
    manual_path = write_manual_review_html(candidates, output_dir, topn=min(max(1, manual_review_topn), len(candidates)))
    return {"run_id": run_id, "output_dir": str(output_dir), "candidate_count": len(candidates), "manual_review_html": manual_path}
