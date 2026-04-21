"""n8n 쇼핑몰 크롤러 대시보드 - Streamlit 탭."""
from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

_API = os.environ.get("CRAWLER_API_URL", "http://localhost:8000")

CRON_PRESETS = {
    "매시간":        "0 * * * *",
    "매일 오전 6시": "0 6 * * *",
    "매일 오전 7시": "0 7 * * *",
    "매일 오전 9시": "0 9 * * *",
    "매일 정오":     "0 12 * * *",
    "매일 오후 6시": "0 18 * * *",
    "매주 월요일":   "0 9 * * 1",
    "매주 수요일":   "0 9 * * 3",
    "매주 금요일":   "0 9 * * 5",
    "직접 입력":     "__custom__",
}

CATEGORY_LABELS = {
    "fashion":     "👗 패션/의류",
    "electronics": "💻 전자제품/디지털",
    "food":        "🥗 식품/건강",
    "beauty":      "💄 뷰티/화장품",
    "furniture":   "🛋️ 가구/인테리어",
    "sports":      "🏋️ 스포츠/레저",
    "baby":        "🍼 육아/완구",
    "pet":         "🐾 반려동물",
}

SORT_LABELS = {
    "newest":     "최신순",
    "price_asc":  "가격 낮은순",
    "price_desc": "가격 높은순",
    "rating":     "평점 높은순",
    "reviews":    "리뷰 많은순",
}

MALL_LABELS = {
    "": "전체",
    "coupang":  "쿠팡",
    "naver":    "네이버쇼핑",
    "gmarket":  "G마켓",
    "11st":     "11번가",
    "ssg":      "SSG닷컴",
    "lotteon":  "롯데온",
}


def _api(method: str, path: str, **kw) -> Any | None:
    try:
        resp = getattr(requests, method)(f"{_API}{path}", timeout=15, **kw)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(f"크롤러 API 서버에 연결할 수 없습니다 ({_API}). docker-compose up 이 실행 중인지 확인하세요.")
        return None
    except Exception as e:
        st.error(f"API 오류: {e}")
        return None


def render_search_tab() -> None:
    st.subheader("상품 검색")
    st.caption("크롤링된 전체 쇼핑몰 데이터에서 통합 검색합니다.")

    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        q = st.text_input("검색어", placeholder="예: 무선 이어폰, 마스크팩, 요가매트")
    with col2:
        category = st.selectbox(
            "카테고리",
            options=[""] + list(CATEGORY_LABELS.keys()),
            format_func=lambda x: "전체 카테고리" if x == "" else CATEGORY_LABELS.get(x, x),
        )
    with col3:
        mall = st.selectbox(
            "쇼핑몰",
            options=list(MALL_LABELS.keys()),
            format_func=lambda x: MALL_LABELS.get(x, x),
        )

    col4, col5, col6, col7 = st.columns(4)
    with col4:
        min_price = st.number_input("최저가 (원)", min_value=0, value=0, step=1000)
    with col5:
        max_price = st.number_input("최고가 (원)", min_value=0, value=0, step=1000, help="0 = 제한 없음")
    with col6:
        sort = st.selectbox("정렬", options=list(SORT_LABELS.keys()), format_func=lambda x: SORT_LABELS[x])
    with col7:
        since_hours = st.number_input("최근 N시간 이내", min_value=0, value=0, help="0 = 전체 기간")

    limit = st.slider("표시 개수", min_value=5, max_value=100, value=20, step=5)

    if st.button("검색", type="primary", use_container_width=True):
        if not q and not category:
            st.warning("검색어 또는 카테고리를 입력해주세요.")
            return

        params: dict[str, Any] = {
            "q": q, "category": category, "mall": mall,
            "min_price": min_price, "max_price": max_price,
            "sort": sort, "limit": limit, "since_hours": since_hours,
        }
        with st.spinner("검색 중..."):
            data = _api("get", "/search", params=params)

        if data is None:
            return

        st.success(f"총 {data.get('total', 0):,}건 검색됨 (표시: {len(data.get('items', []))}건)")
        items = data.get("items", [])
        if not items:
            st.info("검색 결과가 없습니다. 먼저 '크롤 실행' 탭에서 데이터를 수집하세요.")
            return

        for item in items:
            with st.container(border=True):
                c1, c2 = st.columns([1, 4])
                with c1:
                    if item.get("image_url"):
                        st.image(item["image_url"], width=120)
                    else:
                        st.markdown("🖼️ 이미지 없음")
                with c2:
                    price_str = f"{int(item['price']):,}원" if item.get("price") else "가격 미상"
                    st.markdown(f"**{item['title']}**")
                    st.markdown(
                        f"`{MALL_LABELS.get(item.get('mall_id',''), item.get('mall_name',''))}` · "
                        f"`{CATEGORY_LABELS.get(item.get('category_id',''), item.get('category_name',''))}` · "
                        f"**{price_str}**"
                    )
                    if item.get("rating"):
                        st.markdown(f"⭐ {item['rating']} | 리뷰 {item.get('review_count', 0):,}개")
                    if item.get("seller"):
                        st.caption(f"판매자: {item['seller']}")
                    st.link_button("상품 보기", item["url"])


def render_stats_tab() -> None:
    st.subheader("카테고리별 현황")

    if st.button("새로고침", key="stats_refresh"):
        st.cache_data.clear()

    data = _api("get", "/stats")
    if data is None:
        return

    categories = data.get("categories", [])
    if not categories:
        st.info("아직 크롤링된 데이터가 없습니다. '크롤 실행' 탭에서 데이터를 먼저 수집하세요.")
        return

    import pandas as pd
    df = pd.DataFrame(categories)
    df = df.rename(columns={
        "category_name": "카테고리",
        "total": "총 상품",
        "new_today": "오늘 신규",
        "min_price": "최저가",
        "avg_price": "평균가",
        "max_price": "최고가",
        "last_crawled": "최근 크롤",
    })
    if "min_price" in df.columns or "최저가" in df.columns:
        for col in ["최저가", "평균가", "최고가"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"{int(x):,}원" if x else "-")
    st.dataframe(df, use_container_width=True)

    # 총계 메트릭
    total = sum(c.get("total", 0) for c in categories)
    new_today = sum(c.get("new_today", 0) for c in categories)
    col1, col2, col3 = st.columns(3)
    col1.metric("전체 수집 상품", f"{total:,}개")
    col2.metric("오늘 신규", f"{new_today:,}개")
    col3.metric("크롤링 쇼핑몰", len(data.get("malls", [])))

    st.subheader("리포트 보기")
    st.link_button("HTML 리포트 열기", f"{_API}/report/daily", use_container_width=True)


def render_crawl_tab() -> None:
    st.subheader("수동 크롤 실행")
    st.caption("선택한 카테고리를 즉시 크롤링합니다. (n8n 스케줄러와 별개로 실행)")

    category = st.selectbox(
        "카테고리 선택",
        options=list(CATEGORY_LABELS.keys()),
        format_func=lambda x: CATEGORY_LABELS[x],
        key="crawl_category",
    )
    max_items = st.slider("쇼핑몰당 최대 상품 수", 5, 50, 20)

    if st.button("크롤 시작", type="primary"):
        with st.spinner(f"{CATEGORY_LABELS[category]} 크롤링 중... (최대 2분 소요)"):
            result = _api("post", f"/crawl/category/{category}", json={
                "category_id": category,
                "category_name": CATEGORY_LABELS[category].split(" ", 1)[-1],
                "max_items_per_mall": max_items,
            })
        if result:
            st.success(
                f"완료! 신규 {result.get('new_count', 0)}개 · "
                f"업데이트 {result.get('updated_count', 0)}개 · "
                f"총 {result.get('total_count', 0)}개"
            )
            st.json(result)


def render_schedule_tab() -> None:
    st.subheader("크롤 주기 설정")
    st.caption("카테고리별 자동 크롤링 주기를 설정합니다. 변경 후 n8n에서 워크플로우를 재활성화하세요.")

    data = _api("get", "/config/schedules")
    if data is None:
        return

    for sched in data:
        cat_id = sched["category_id"]
        label = CATEGORY_LABELS.get(cat_id, cat_id)
        with st.expander(f"{label} · 현재: `{sched['cron_expression']}`", expanded=False):
            col1, col2 = st.columns([2, 1])
            with col1:
                preset_key = st.selectbox(
                    "주기 선택",
                    options=list(CRON_PRESETS.keys()),
                    key=f"preset_{cat_id}",
                )
            with col2:
                enabled = st.toggle(
                    "활성화",
                    value=bool(sched.get("enabled", True)),
                    key=f"enabled_{cat_id}",
                )

            cron = CRON_PRESETS[preset_key]
            if cron == "__custom__":
                cron = st.text_input(
                    "직접 입력 (cron)",
                    value=sched["cron_expression"],
                    key=f"custom_{cat_id}",
                    help="형식: 분 시 일 월 요일  예) 0 9 * * 1 (매주 월요일 오전 9시)",
                )

            if st.button("저장", key=f"save_{cat_id}"):
                result = _api("put", f"/config/schedule/{cat_id}", json={
                    "cron_expression": cron,
                    "enabled": enabled,
                })
                if result:
                    st.success(f"저장 완료: `{cron}` {'활성' if enabled else '비활성'}")
                    st.rerun()


def render_n8n_tab() -> None:
    st.subheader("n8n 워크플로우 가이드")
    st.markdown("""
### 설치 및 시작
```bash
# 전체 시스템 시작
cd n8n
docker-compose up -d

# n8n 접속
open http://localhost:5678
# ID: admin / PW: changeme123 (docker-compose.yml 에서 변경 가능)
```

### 워크플로우 가져오기 (Import)
1. n8n 접속 → **Workflows** 메뉴
2. **Import from file** 클릭
3. `n8n/workflows/` 폴더의 JSON 파일 3개를 순서대로 import

| 파일 | 역할 |
|------|------|
| `01_main_scheduler.json` | 전체 스케줄 관리, 카테고리 순회, Slack 알림 |
| `02_category_crawler.json` | 카테고리별 쇼핑몰 크롤링 (Webhook 수신) |
| `03_search_api.json` | 검색 API, 스케줄 조회/수정 Webhook |

### 검색 API 엔드포인트
```
GET http://localhost:5678/webhook/search
  ?q=무선이어폰
  &category=electronics
  &mall=coupang
  &min_price=10000
  &max_price=100000
  &sort=price_asc
  &limit=20
  &since_hours=24      ← 최근 24시간 내 크롤된 상품만
```

### 스케줄 관리 API
```bash
# 전체 스케줄 조회
GET http://localhost:5678/webhook/schedule

# 특정 카테고리 스케줄 변경
PUT http://localhost:5678/webhook/schedule
Body: { "category_id": "fashion", "cron_expression": "0 8 * * *", "enabled": true }
```
""")

    st.subheader("크롤러 API 직접 접속")
    st.link_button("API 문서 (Swagger UI) 열기", f"{_API}/docs", use_container_width=True)
    st.link_button("HTML 리포트 보기", f"{_API}/report/daily", use_container_width=True)
