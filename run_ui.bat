@echo off
cd /d %~dp0
if not exist .venv (
  py -3.11 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -e .[ui]
python -m playwright install chromium
start "sachyo UI" cmd /k "streamlit run src/ui/app.py"
