@echo off
cd /d %~dp0
if not exist .venv (
  py -3.11 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -e .
python -m src.main run --image .\input.jpg --query_hint "제품명 모델명" --sources coupang,naver,11st,gmarket,auction,ssg,lotteon,wemakeprice,tmon,interpark --output_dir .\output
pause
