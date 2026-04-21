from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from crawlers import CRAWLERS
from db import (
    get_category_stats,
    get_schedules,
    init_db,
    save_daily_report,
    search_products,
    update_schedule,
    upsert_products,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "fashion":     ["패션 의류", "신발", "가방", "액세서리", "원피스"],
    "electronics": ["스마트폰", "노트북", "이어폰", "가전제품", "태블릿"],
    "food":        ["건강식품", "간편식", "과자 음료", "커피", "유기농"],
    "beauty":      ["화장품", "스킨케어", "마스크팩", "향수", "선크림"],
    "furniture":   ["가구", "소파", "책상 조명", "커튼", "침대"],
    "sports":      ["운동기구", "요가매트", "등산용품", "자전거", "헬스용품"],
    "baby":        ["기저귀", "분유", "유모차", "장난감", "아동복"],
    "pet":         ["강아지사료", "고양이사료", "펫용품", "리드줄", "펫하우스"],
}

MALL_ENDPOINTS: dict[str, str] = {
    "coupang":  "coupang",
    "naver":    "naver",
    "gmarket":  "gmarket",
    "elevenst": "elevenst",
    "ssg":      "ssg",
    "lotteon":  "lotteon",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    log.info("DB initialized")
    yield


app = FastAPI(
    title="쇼핑몰 크롤러 API",
    description="n8n 워크플로우와 연동되는 쇼핑몰 카테고리별 크롤링 백엔드",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 요청/응답 모델 ──────────────────────────────────────────────────────────────

class CrawlCategoryRequest(BaseModel):
    category_id: str
    category_name: str = ""
    max_items_per_mall: int = 30


class CrawlMallRequest(BaseModel):
    category_id: str
    category_name: str = ""
    mall_id: str
    keywords: list[str]
    primary_keyword: str = ""
    max_items: int = 30


class SaveResultsRequest(BaseModel):
    category_id: str
    category_name: str = ""
    products: list[dict[str, Any]]
    crawled_at: str = ""


class ScheduleUpdateRequest(BaseModel):
    cron_expression: str | None = None
    enabled: bool | None = None


class DailyReportRequest(BaseModel):
    crawled_at: str
    total_categories: int
    total_new_items: int
    total_updated_items: int
    category_results: list[dict[str, Any]]


# ── 엔드포인트 ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.post("/crawl/category/{category_id}")
def crawl_category(category_id: str, req: CrawlCategoryRequest) -> dict[str, Any]:
    """카테고리 전체 쇼핑몰 동시 크롤링."""
    keywords = CATEGORY_KEYWORDS.get(category_id, [req.category_name or category_id])
    category_name = req.category_name or category_id

    all_products: list[dict[str, Any]] = []
    malls_crawled: list[str] = []
    errors: list[str] = []

    for mall_key, endpoint in MALL_ENDPOINTS.items():
        crawler_cls = CRAWLERS.get(endpoint)
        if not crawler_cls:
            continue
        try:
            crawler = crawler_cls()
            products = crawler.crawl(category_id, category_name, keywords, req.max_items_per_mall)
            all_products.extend(p.to_dict() for p in products)
            malls_crawled.append(mall_key)
            log.info("crawled mall=%s category=%s count=%d", mall_key, category_id, len(products))
        except Exception as e:
            errors.append(f"{mall_key}: {e}")
            log.exception("crawl error mall=%s category=%s", mall_key, category_id)

    new_count, updated_count = upsert_products(all_products)
    return {
        "category_id": category_id,
        "category_name": category_name,
        "total_count": len(all_products),
        "new_count": new_count,
        "updated_count": updated_count,
        "malls_crawled": malls_crawled,
        "errors": errors,
        "crawled_at": datetime.utcnow().isoformat(),
    }


@app.post("/crawl/mall/{endpoint}")
def crawl_mall(endpoint: str, req: CrawlMallRequest) -> dict[str, Any]:
    """특정 쇼핑몰 단독 크롤링 (n8n 카테고리 크롤러 워크플로우에서 호출)."""
    crawler_cls = CRAWLERS.get(endpoint)
    if not crawler_cls:
        raise HTTPException(status_code=404, detail=f"알 수 없는 쇼핑몰: {endpoint}")

    crawler = crawler_cls()
    keywords = req.keywords or [req.primary_keyword or req.category_id]
    try:
        products = crawler.crawl(req.category_id, req.category_name, keywords, req.max_items)
    except Exception as e:
        log.exception("crawl error endpoint=%s", endpoint)
        raise HTTPException(status_code=500, detail=str(e))

    new_count, updated_count = upsert_products([p.to_dict() for p in products])
    return {
        "category_id": req.category_id,
        "category_name": req.category_name,
        "mall_id": crawler.mall_id,
        "mall_name": crawler.mall_name,
        "total_count": len(products),
        "new_count": new_count,
        "updated_count": updated_count,
        "products": [p.to_dict() for p in products],
        "crawled_at": datetime.utcnow().isoformat(),
    }


@app.post("/results/save")
def save_results(req: SaveResultsRequest) -> dict[str, Any]:
    """n8n 워크플로우에서 직접 가공한 결과를 저장."""
    for p in req.products:
        p.setdefault("category_id", req.category_id)
        p.setdefault("category_name", req.category_name)
    new_count, updated_count = upsert_products(req.products)
    return {
        "saved": len(req.products),
        "new_count": new_count,
        "updated_count": updated_count,
    }


@app.get("/search")
def search(
    q: str = Query(default="", description="검색어 (FTS 지원)"),
    category: str = Query(default="", description="카테고리 ID"),
    mall: str = Query(default="", description="쇼핑몰 ID"),
    min_price: float = Query(default=0, ge=0),
    max_price: float = Query(default=0, ge=0),
    sort: str = Query(default="newest", description="정렬: newest|price_asc|price_desc|rating|reviews"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    since_hours: int = Query(default=0, ge=0, description="최근 N시간 내 크롤링된 상품만"),
) -> dict[str, Any]:
    return search_products(
        q=q, category=category, mall=mall,
        min_price=min_price, max_price=max_price,
        sort=sort, limit=limit, offset=offset,
        since_hours=since_hours,
    )


@app.get("/stats")
def stats() -> dict[str, Any]:
    return {
        "categories": get_category_stats(),
        "malls": list(MALL_ENDPOINTS.keys()),
        "crawled_at": datetime.utcnow().isoformat(),
    }


@app.get("/config/schedules")
def list_schedules() -> list[dict[str, Any]]:
    return get_schedules()


@app.put("/config/schedule/{category_id}")
def update_category_schedule(category_id: str, req: ScheduleUpdateRequest) -> dict[str, Any]:
    result = update_schedule(category_id, req.cron_expression, req.enabled)
    if not result:
        raise HTTPException(status_code=404, detail=f"카테고리 없음: {category_id}")
    return result


@app.post("/report/daily")
def save_report(req: DailyReportRequest) -> dict[str, str]:
    save_daily_report(req.model_dump())
    return {"status": "saved", "date": datetime.utcnow().strftime("%Y-%m-%d")}


@app.get("/report/daily", response_class=HTMLResponse)
def get_daily_report_html() -> str:
    """오늘 크롤링 결과를 HTML 리포트로 반환."""
    stats_data = get_category_stats()
    schedules = get_schedules()

    schedule_map = {s["category_id"]: s["cron_expression"] for s in schedules}

    rows = "\n".join(
        f"""<tr>
          <td>{s['category_name']}</td>
          <td>{s['total']:,}</td>
          <td style='color:green'>{s['new_today']:,}</td>
          <td>{int(s['min_price'] or 0):,}원</td>
          <td>{int(s['avg_price'] or 0):,}원</td>
          <td>{int(s['max_price'] or 0):,}원</td>
          <td>{s['last_crawled'] or '-'}</td>
          <td><code>{schedule_map.get(s['category_id'], '-')}</code></td>
        </tr>"""
        for s in stats_data
    )
    return f"""<!DOCTYPE html>
<html lang='ko'>
<head>
  <meta charset='utf-8'>
  <title>쇼핑몰 크롤러 리포트</title>
  <style>
    body {{ font-family: 'Noto Sans KR', sans-serif; margin: 2rem; background: #f8f9fa; }}
    h1 {{ color: #2c3e50; }} h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 4px; }}
    table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.1); }}
    th {{ background: #3498db; color: white; padding: 10px 14px; text-align: left; }}
    td {{ padding: 9px 14px; border-bottom: 1px solid #ecf0f1; }}
    tr:hover {{ background: #f0f8ff; }}
    .badge {{ display:inline-block; padding:2px 8px; border-radius:12px; background:#e8f5e9; color:#2e7d32; font-size:.85em; }}
  </style>
</head>
<body>
  <h1>🛒 쇼핑몰 크롤러 리포트</h1>
  <p>생성: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
  <h2>카테고리별 현황</h2>
  <table>
    <thead>
      <tr><th>카테고리</th><th>총 상품</th><th>오늘 신규</th>
          <th>최저가</th><th>평균가</th><th>최고가</th>
          <th>최근 크롤</th><th>스케줄(Cron)</th></tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <br>
  <h2>사용 가능한 쇼핑몰</h2>
  <p>{' '.join(f'<span class="badge">{m}</span>' for m in MALL_ENDPOINTS)}</p>
  <h2>검색 API</h2>
  <pre>GET /search?q=키워드&amp;category=fashion&amp;mall=coupang&amp;min_price=1000&amp;max_price=50000&amp;sort=price_asc&amp;limit=20</pre>
</body>
</html>"""


@app.get("/categories")
def list_categories() -> list[dict[str, Any]]:
    return [
        {"id": k, "keywords": v[:3], "keyword_count": len(v)}
        for k, v in CATEGORY_KEYWORDS.items()
    ]
