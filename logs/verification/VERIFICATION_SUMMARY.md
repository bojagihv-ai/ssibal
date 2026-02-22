# 실행 검증 요약

## 환경
- Python: 3.10.19 (요구사항 3.11+ 미충족)

## CLI 검증
- 명령: `python -m src.main run --image ./input.jpg --query_hint "제품명 모델명" --sources coupang,naver,11st,gmarket,auction,ssg,lotteon,wemakeprice,tmon,interpark --output_dir ./output`
- 결과: 실패
- 원인: `ModuleNotFoundError: No module named 'src'`

## UI 검증
- 명령: `streamlit run src/ui/app.py`
- 결과: 실패
- 원인: `streamlit` 명령 없음 + `src/ui/app.py` 미존재

## 다음 액션
1. Python 3.11 이상 설치
2. 프로젝트 실제 소스(`src/`) 반영
3. `pip install -e .[ui]` 실행
4. Playwright Chromium 설치 후 재검증
