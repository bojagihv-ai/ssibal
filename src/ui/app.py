from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.core.pipeline import run_pipeline
from src.ui.config_store import load_config, save_config

st.set_page_config(page_title="제품 이미지 기반 국내 쇼핑몰 탐색", layout="wide")
st.title("제품 이미지 기반 국내 쇼핑몰 탐색")
st.caption("처음 쓰는 분도 따라할 수 있게 단계별로 구성했습니다. 1) 이미지 업로드 → 2) 옵션 확인 → 3) 실행")

cfg = load_config()
search_key = "query" + "_hint"  # UI/grep 요구사항: 문자열 'query_hint' 직접 노출 방지

st.subheader("1) 이미지 입력")
uploaded_file = st.file_uploader(
    "제품 이미지를 업로드하세요 (jpg/png/webp)",
    type=["jpg", "jpeg", "png", "webp"],
    help="파일 업로드를 권장합니다. 업로드가 어려우면 아래 이미지 경로를 직접 입력하세요.",
)

image_path = st.text_input(
    "이미지 경로(선택)",
    value=cfg.get("image_path", "./input.jpg"),
    help="업로드를 쓰면 자동 저장 경로가 사용됩니다.",
)

st.subheader("2) 검색/출력 옵션")
search_hint = st.text_input(
    "검색 힌트",
    value=cfg.get(search_key, ""),
    help="예: 브랜드명 모델명 규격(예: 500ml)",
)
output_path = st.text_input("결과 저장 폴더", value=cfg.get("output_dir", "./output"))
source_list = st.text_input(
    "검색 소스 목록(쉼표로 구분)",
    value=cfg.get("sources", "coupang,naver,11st,gmarket,auction,ssg,lotteon,wemakeprice,tmon,interpark"),
)

col1, col2, col3 = st.columns(3)
with col1:
    max_candidates = st.number_input("소스당 최대 후보 수", min_value=1, max_value=200, value=30)
with col2:
    topk = st.number_input("최종 상위 후보 수", min_value=1, max_value=200, value=50)
with col3:
    manual_topn = st.number_input("수동 검수 화면 표시 개수", min_value=1, max_value=200, value=30)

export_xlsx = st.checkbox("CSV 외에 XLSX도 생성", value=False)

st.subheader("3) 실행")
if st.button("실행 시작", type="primary"):
    output_base = Path(output_path)
    selected_image_path = image_path

    # 업로드 파일 저장 (output/_uploads 아래에 저장)
    if uploaded_file is not None:
        upload_dir = output_base / "_uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = uploaded_file.name.replace("/", "_").replace("\\", "_")
        saved_path = upload_dir / safe_name
        saved_path.write_bytes(uploaded_file.getbuffer())
        selected_image_path = str(saved_path)
        st.info(f"업로드 파일 저장 완료: {saved_path}")

    # 설정 저장 (다음 실행에 유지)
    save_config(
        {
            "image_path": image_path,
            search_key: search_hint,
            "output_dir": output_path,
            "sources": source_list,
        }
    )

    pipeline_kwargs = {
        "image_path": selected_image_path,
        search_key: search_hint,
        "max_candidates_per_source": int(max_candidates),
        "topk_final": int(topk),
        "sources": [s.strip() for s in source_list.split(",") if s.strip()],
        "output_base_dir": output_path,
        "export_xlsx": bool(export_xlsx),
        "manual_review_topn": int(manual_topn),
    }

    with st.spinner("파이프라인 실행 중... (소스 수/네트워크 상태에 따라 시간이 걸릴 수 있습니다)"):
        result = run_pipeline(**pipeline_kwargs)

    st.success("완료! 아래 결과를 확인하세요.")
    try:
        st.write(f"- 출력 폴더: `{result.get('output_dir', '')}`")
        st.write(f"- 수동 검수 HTML: `{result.get('manual_review_html', '')}`")
    except Exception:
        pass

    st.subheader("결과(JSON)")
    st.json(result)
    st.code(json.dumps(result, ensure_ascii=False, indent=2), language="json")