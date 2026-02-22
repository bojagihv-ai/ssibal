from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.pipeline import run_pipeline

TINY_PNG = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Z1ioAAAAASUVORK5CYII="


def main() -> None:
    work = Path(".tmp_validate")
    work.mkdir(exist_ok=True)
    img = work / "input.png"
    img.write_bytes(base64.b64decode(TINY_PNG))

    result = run_pipeline(
        image_path=str(img),
        query_hint="검수 테스트 500ml",
        max_candidates_per_source=3,
        topk_final=4,
        sources=["demo1", "demo2"],
        output_base_dir=str(work / "output"),
        manual_review_topn=3,
    )
    out = Path(result["output_dir"])
    required = [
        out / "run_config.json",
        out / "reports" / "candidates.csv",
        out / "reports" / "verified.csv",
        out / "reports" / "leaderboards.csv",
        out / "reports" / "manual_review.html",
    ]
    status = {str(p): p.exists() for p in required}
    print(json.dumps({"result": result, "checks": status}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
