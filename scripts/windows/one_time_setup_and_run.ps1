param(
  [Parameter(Mandatory=$false)]
  [string]$ImagePath = ".\\input.jpg",

  [Parameter(Mandatory=$false)]
  [string]$QueryHint = "제품명 모델명",

  [Parameter(Mandatory=$false)]
  [string]$OutputDir = ".\\output"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path ".\\logs\\verification" | Out-Null

function Write-Step($msg) {
  Write-Host "`n==== $msg ====" -ForegroundColor Cyan
}

Write-Step "1) Python 버전 확인"
python --version | Tee-Object -FilePath ".\\logs\\verification\\python_version.log"

Write-Step "2) 가상환경 생성"
if (-not (Test-Path ".\\.venv")) {
  python -m venv .venv
}

Write-Step "3) 가상환경 활성화"
. .\\.venv\\Scripts\\Activate.ps1

Write-Step "4) pip 업그레이드"
python -m pip install --upgrade pip | Tee-Object -FilePath ".\\logs\\verification\\pip_upgrade.log"

Write-Step "5) 의존성 설치"
pip install -e .[ui] | Tee-Object -FilePath ".\\logs\\verification\\pip_install.log"

Write-Step "6) Playwright Chromium 설치"
python -m playwright install chromium | Tee-Object -FilePath ".\\logs\\verification\\playwright_install.log"

Write-Step "7) CLI 실행"
$cliCmd = "python -m src.main run --image $ImagePath --query_hint `"$QueryHint`" --sources coupang,naver,11st,gmarket,auction,ssg,lotteon,wemakeprice,tmon,interpark --output_dir $OutputDir"
Write-Host $cliCmd -ForegroundColor Yellow
Invoke-Expression $cliCmd | Tee-Object -FilePath ".\\logs\\verification\\cli_attempt.log"

Write-Step "8) UI 실행(수동 시작용 명령만 안내)"
Write-Host "streamlit run src/ui/app.py" -ForegroundColor Yellow
Write-Host "원하면 아래 명령으로 바로 실행하세요:" -ForegroundColor Green
Write-Host "streamlit run src/ui/app.py 2>&1 | Tee-Object .\\logs\\verification\\ui_attempt.log" -ForegroundColor Green

Write-Step "완료"
Write-Host "로그 폴더: .\\logs\\verification" -ForegroundColor Green
