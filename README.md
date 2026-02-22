# sachyo

제품 이미지 1장으로 국내 쇼핑몰 후보를 수집/분류/검수하고 리포트(CSV/XLSX)와 상세 이미지 아카이브를 생성하는 도구입니다.

## 현재 진행 상태(진행률)
- 완료: CLI, 파이프라인, CSV 리포트, 수동 검수 HTML, Windows 더블클릭 실행 배치, 바탕화면 아이콘 생성 스크립트, 데모 검증 스크립트
- 진행 중: 실서비스 소스(Coupang/Naver)의 현행 DOM 변동 대응 강화, OCR/고급 임베딩 고도화

## 설계 요약
- **데이터 스키마**: `ListingCandidate`, `ListingMeta`, `DownloadResult`, `VerifyResult` (`src/core/models.py`)
- **핵심 흐름**: 입력 이미지 + query_hint → 소스별 후보 수집 → 유사도/3단계 분류 → 10체크 검수 요약 → 상세 이미지 수집 → CSV/XLSX/수동검수 HTML 생성 (`src/core/pipeline.py`)
- **어댑터 구조**: `BaseAdapter` 인터페이스 + `CoupangAdapter`, `NaverSmartstoreAdapter`, 기타 소스는 `DemoAdapter`로 확장 가능 (`src/adapters/*`)

## 설치
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[ui]
python -m playwright install chromium
```

## CLI 실행
> 옵션명은 반드시 `--query_hint`, `--output_dir` (언더스코어)

```bash
python -m src.main run --image ./input.jpg --query_hint "제품명 모델명" --sources coupang,naver,11st,gmarket,auction,ssg,lotteon,wemakeprice,tmon,interpark --output_dir ./output --manual_review_topn 30
```

## UI 실행
```bash
streamlit run src/ui/app.py
```

## Windows 초보자용 실행
- `run_ui.bat`: 더블클릭으로 UI 준비/실행
- `run_cli.bat`: 더블클릭으로 CLI 예시 실행
- 바탕화면 아이콘 생성:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\create_shortcuts.ps1
```

## 검증(권장)
```bash
python scripts/validate_demo_run.py
```

## 출력 구조
```text
output/{run_id}/
  run.log
  run_config.json
  reports/
    candidates.csv
    verified.csv
    leaderboards.csv
    manual_review.html
    reports.xlsx (옵션)
  assets/{platform}/{item_id}/
    detail_images/*
    page_snapshot.html
    page_full.png
    download_manifest.json
```

## ToS/안전
- 로그인/결제/캡차 회피/우회 기능은 구현하지 않았습니다.
- 요청 실패는 `run.log`에 단계별 에러로 남깁니다.
- 사이트 정책 준수를 위해 요청량(rate-limit/backoff)을 통제해서 사용하세요.
