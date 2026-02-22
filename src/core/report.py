from __future__ import annotations

import csv
from pathlib import Path

from src.core.models import ListingCandidate


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_manual_review_html(candidates: list[ListingCandidate], output_dir: Path, topn: int = 30) -> str:
    rows = sorted(candidates, key=lambda c: c.confidence, reverse=True)[:topn]
    html = [
        "<html><head><meta charset='utf-8'><title>sachyo manual review</title></head><body>",
        "<h2>sachyo 수동 검수 리포트</h2>",
        "<p>체크박스로 동일제품 여부를 사람이 확인하세요(참고용).</p>",
        "<table border='1' cellspacing='0' cellpadding='6'>",
        "<tr><th>확인</th><th>이미지</th><th>플랫폼</th><th>제목</th><th>가격</th><th>confidence</th><th>링크</th></tr>",
    ]
    for c in rows:
        img_html = f"<img src='{c.image_url}' width='120' />" if c.image_url else '-'
        html.append(
            "<tr>"
            f"<td><input type='checkbox' /></td>"
            f"<td>{img_html}</td>"
            f"<td>{c.platform}</td>"
            f"<td>{c.title}</td>"
            f"<td>{c.price if c.price is not None else '-'} </td>"
            f"<td>{c.confidence}</td>"
            f"<td><a href='{c.url}' target='_blank'>open</a></td>"
            "</tr>"
        )
    html.append("</table></body></html>")
    path = output_dir / "reports" / "manual_review.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(html), encoding="utf-8")
    return str(path)


def write_reports(candidates: list[ListingCandidate], output_dir: Path, export_xlsx: bool = False) -> None:
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    rows = [c.to_dict() for c in candidates]
    fields = sorted({k for r in rows for k in r.keys()}) if rows else ["platform", "url", "title", "similarity_score"]
    _write_csv(reports_dir / "candidates.csv", rows, fields)

    verified_rows = [r for r in rows if r.get("verified_flag")]
    _write_csv(reports_dir / "verified.csv", verified_rows, fields)

    leaderboards = []
    by_price = sorted([r for r in rows if isinstance(r.get("price"), (int, float))], key=lambda x: x["price"])[:10]
    by_reviews = sorted([r for r in rows if isinstance(r.get("review_count"), (int, float))], key=lambda x: x["review_count"], reverse=True)[:10]
    by_sales = sorted([r for r in rows if isinstance(r.get("sales_metric"), (int, float))], key=lambda x: x["sales_metric"], reverse=True)[:10]
    by_conf = sorted(rows, key=lambda x: x.get("confidence", 0), reverse=True)[:10]
    for bname, data in [("lowest_price", by_price), ("top_reviews", by_reviews), ("top_sales_metric", by_sales), ("top_confidence", by_conf)]:
        for r in data:
            x = dict(r)
            x["board"] = bname
            leaderboards.append(x)
    lb_fields = sorted({k for r in leaderboards for k in r.keys()}) if leaderboards else fields + ["board"]
    _write_csv(reports_dir / "leaderboards.csv", leaderboards, lb_fields)

    if export_xlsx:
        try:
            import pandas as pd

            pd.DataFrame(rows).to_excel(reports_dir / "reports.xlsx", index=False)
        except Exception:
            pass
