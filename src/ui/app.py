from __future__ import annotations

import json

import streamlit as st

from src.core.pipeline import run_pipeline
from src.ui.config_store import load_config, save_config

st.set_page_config(page_title="sachyo", layout="wide")
st.title("sachyo - 제품 이미지 기반 국내 쇼핑몰 탐색")

cfg = load_config()
image_path = st.text_input("이미지 경로", value=cfg.get("image_path", "./input.jpg"))
query_hint = st.text_input("query_hint", value=cfg.get("query_hint", ""))
output_dir = st.text_input("output_dir", value=cfg.get("output_dir", "./output"))
sources = st.text_input(
    "sources (comma separated)",
    value=cfg.get("sources", "coupang,naver,11st,gmarket,auction,ssg,lotteon,wemakeprice,tmon,interpark"),
)
max_candidates = st.number_input("max_candidates_per_source", min_value=1, max_value=200, value=30)
topk = st.number_input("topk_final", min_value=1, max_value=200, value=50)
export_xlsx = st.checkbox("xlsx 생성", value=False)
manual_topn = st.number_input("manual_review_topn", min_value=1, max_value=200, value=30)

if st.button("실행"):
    save_config({"image_path": image_path, "query_hint": query_hint, "output_dir": output_dir, "sources": sources})
    with st.spinner("파이프라인 실행 중..."):
        result = run_pipeline(
            image_path=image_path,
            query_hint=query_hint,
            max_candidates_per_source=int(max_candidates),
            topk_final=int(topk),
            sources=[s.strip() for s in sources.split(",") if s.strip()],
            output_base_dir=output_dir,
            export_xlsx=export_xlsx,
            manual_review_topn=int(manual_topn),
        )
    st.success("완료")
    st.json(result)
    st.code(json.dumps(result, ensure_ascii=False, indent=2), language="json")
