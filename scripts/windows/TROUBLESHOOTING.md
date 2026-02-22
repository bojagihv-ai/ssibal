# Windows PowerShell 에러 대응표

아래는 sachyo 실행 시 자주 만나는 오류와 해결 방법입니다.

| 에러 메시지(예시) | 원인 | 해결 방법 |
|---|---|---|
| `python: command not found` / `python is not recognized` | Python 미설치 또는 PATH 미등록 | Python 3.11+ 설치 후 `Add python.exe to PATH` 체크. 새 터미널 재실행 |
| `running scripts is disabled on this system` | PowerShell 실행 정책 제한 | 관리자 권한 또는 현재 세션에서 `Set-ExecutionPolicy -Scope Process Bypass` 후 재시도 |
| `No module named pip` | Python 설치 불완전 | `python -m ensurepip --upgrade` 실행 후 `python -m pip install --upgrade pip` |
| `No module named src.main` | 프로젝트 소스(`src/`) 부재 또는 잘못된 경로 | 저장소 루트에서 실행 확인. 실제 코드가 체크아웃되었는지 확인 |
| `Invalid value: File does not exist: src/ui/app.py` | UI 파일 부재 | 저장소에 UI 소스 존재 여부 확인 후 재실행 |
| `ModuleNotFoundError: No module named 'playwright'` | 의존성 미설치 | `pip install -e .[ui]` 또는 `pip install playwright` |
| `Executable doesn't exist ... chromium` | 브라우저 바이너리 미설치 | `python -m playwright install chromium` |
| `PermissionError` on `.venv` | 보안 솔루션/권한 문제 | 관리자 PowerShell로 시도 또는 권한 있는 경로(예: 사용자 홈)로 이동 |
| SSL/Proxy 설치 오류 | 사내망/프록시 이슈 | `pip --proxy`, `HTTP_PROXY/HTTPS_PROXY` 설정 후 재설치 |

---

## 빠른 자가 점검 순서

1. `python --version` (3.11 이상인지)
2. `.\.venv\Scripts\Activate.ps1` 활성화 여부
3. `pip install -e .[ui]` 성공 여부
4. `python -m playwright install chromium` 성공 여부
5. `src/main.py`, `src/ui/app.py` 파일 존재 여부

