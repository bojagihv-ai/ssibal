from __future__ import annotations

import base64
from pathlib import Path

from src.core.pipeline import run_pipeline


TINY_PNG = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Z1ioAAAAASUVORK5CYII="


def test_pipeline_smoke(tmp_path: Path):
    img = tmp_path / "input.png"
    img.write_bytes(base64.b64decode(TINY_PNG))

    result = run_pipeline(
        image_path=str(img),
        query_hint="테스트 제품 500ml",
        max_candidates_per_source=2,
        topk_final=3,
        sources=["demo1", "demo2"],
        output_base_dir=str(tmp_path / "out"),
        manual_review_topn=2,
    )
    out_dir = Path(result["output_dir"])
    assert (out_dir / "reports" / "candidates.csv").exists()
    assert (out_dir / "reports" / "manual_review.html").exists()
    assert (out_dir / "run_config.json").exists()
