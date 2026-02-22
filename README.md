# sachyo

제품 이미지 1장으로 국내 쇼핑몰 후보를 수집/분류/검수하고 리포트(CSV/XLSX)와 상세 이미지 아카이브를 생성하는 도구입니다.

## 설치
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[ui]
python -m playwright install chromium
