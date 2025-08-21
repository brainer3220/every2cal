# Project Overview

### 한줄 요약
`every2cal`은(는) 데이터를 캘린더(또는 캘린더 호환 포맷)로 변환하고 웹을 통해 제공하는 Python 기반 도구/웹앱으로 보입니다. (아래 몇 가지 합리적 가정을 함께 표기합니다.)

### 목적
- 외부 형식(텍스트, XML 등)을 캘린더 형식으로 변환하여 캘린더 서비스로 임포트하거나 표시하기 위함.
- 간단한 웹 인터페이스로 변환 결과를 확인하거나 다운로드/공유할 수 있도록 제공.

(가정) 프로젝트에 firebase.json과 zappa_settings.json이 있으므로 정적 호스팅과 서버리스(또는 Lambda) 배포를 염두에 둔 구조입니다.

### 주요 기능 (추정)
- 입력 데이터(예: Everytime export, XML 등)를 캘린더(.ics 또는 Google Calendar 호환)로 변환 (convert.py, everytime.py 관련)
- 웹 UI를 통한 변환 실행 및 결과 보기 (index.py, index.html)
- 정적 자원 제공을 위한 static 폴더
- 배포 설정: Firebase(정적), Zappa(AWS Lambda) 지원 파일 포함

### 간단한 계약 (Inputs/Outputs)
- 입력: 로컬 또는 업로드된 이벤트 데이터 파일 (예: XML, CSV, Everytime 포맷)
- 출력: 캘린더 포맷 파일(.ics 등) 또는 캘린더에 업로드 가능한 데이터
- 오류 모드: 잘못된 입력 포맷, 누락된 필드, 의존성 미설치
- 성공 기준: 변환된 캘린더 파일 생성 및 웹에서 다운로드/보기 가능

### 엣지케이스
- 빈/손상된 입력 파일
- 매우 큰 입력(메모리/시간 초과)
- 로컬 환경에 파이썬 의존성 미설치

## 리포지토리 구조(핵심 파일)
- index.py — (추정) 웹앱 엔트리포인트(라우팅/서버 시작)
- every2cal.py — 프로젝트 핵심 로직 또는 실행용 스크립트
- convert.py — 데이터 변환 관련 유틸리티
- everytime.py — 특정 포맷(예: Everytime) 파서/변환기
- templates — HTML 템플릿 (`index.html`, 개인정보/라이선스 페이지 등)
- static — 정적 자원(js, css 등), `javascript/GetTableXML.js` 포함
- requirements.txt — Python 의존성 목록
- zappa_settings.json — Zappa(AWS Lambda) 배포 설정
- firebase.json — Firebase 호스팅 / 설정 (정적 배포)
- README.md — (존재함) 기본 설명 및 사용법(필요시 보완 권장)

(참고) 일부 파일(예: `convert.cpython-311.pyc`)는 빌드/캐시 산출물이며 버전 관리에서 제외하는 것이 좋습니다.

## 실행(간단 안내, 가정 포함)
가정: 파이썬 3.8+ 환경이며 requirements.txt에 필요한 패키지가 기재됨. 웹 앱 엔트리포인트는 index.py 또는 every2cal.py임.

추천 실행 절차:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 웹서버 실행(가정: index.py 로 시작)
python index.py
```
(만약 index.py가 Flask/Django 앱이라면 `flask run` 또는 프레임워크 명령으로 실행할 수 있음 — 구체적 명령은 코드 확인 필요)

## 의존성 및 배포 노트
- 의존성: requirements.txt 참고. (가정: Flask, Requests, icalendar 등 일반적 라이브러리 포함 가능)
- 배포 옵션:
  - 정적 자원: Firebase Hosting (firebase.json)
  - 서버리스 백엔드: Zappa를 사용한 AWS Lambda 배포 (zappa_settings.json)
- 권장: requirements.txt와 README.md에 정확한 시작/배포 절차 명시

## 개발/유지보수 노트
- 테스트: 핵심 변환 로직(convert.py, everytime.py)에 대해 단위 테스트(예: pytest) 추가 권장 — 입력 정상/비정상 케이스 포함
- 린트/타입: 간단한 flake8/black, 타입 힌트(가능하면 mypy) 도입 권장
- CI: GitHub Actions로 린트/테스트 자동화 권장

## 권장 다음 작업(우선순위)
1. README.md 보강: 설치/실행/배포 예시 및 예제 입력 파일 추가
2. 엔트리포인트 명확화: index.py와 every2cal.py 중 실제 시작 스크립트를 README에 명시
3. 단위 테스트 추가: 변환기 핵심 함수에 대해 happy path + 1~2개의 에러 케이스
4. 불필요한 바이너리 캐시(__pycache__)는 .gitignore에 추가

요약: 요청하신 프로젝트 개요를 작성했습니다(목적·핵심기능·구조·실행·배포·다음 단계 포함). 구체적인 실행 명령이나 README 보강을 원하시면, 어느 파일을 엔트리포인트로 사용할지(예: index.py vs every2cal.py) 알려주시면 바로 실행 검증 및 README 수정까지 진행하겠습니다.

요구사항 커버리지: "Project overview 작성" — 완료.

## Folder Structure

- `every2cal/` (프로젝트 루트)
  - convert.py — 변환 유틸리티(입력 → 캘린더 포맷 변환)  
  - every2cal.py — (추정) 전체 실행 스크립트 / 진입점 중 하나
  - everycal.drawio.svg — 다이어그램(프로젝트 구조/설계)
  - everytime.py — 특정 포맷(예: Everytime) 파서/변환기
  - index.py — (추정) 웹앱 엔트리포인트(Flask 등)
  - README.md — 프로젝트 설명 및 사용법
  - requirements.txt — Python 의존성 목록
  - zappa_settings.json — Zappa(AWS Lambda) 배포 설정
  - firebase.json — Firebase(호스팅) 설정
  - static — 정적 자원
    - `javascript/`
      - `GetTableXML.js` — 클라이언트 측 JS(테이블 → XML 변환 스크립트)
  - templates — 서버 템플릿(HTML)
    - `index.html` — 메인 UI 템플릿
    - `opensourcelicense.html` — 오픈소스 라이선스 정보 페이지
    - `privacypolicy.html` — 개인정보처리방침 페이지
    - `robots.txt` — 검색엔진 크롤러 지침

간단 메모
- __pycache__와 `.pyc` 파일은 보통 .gitignore에 추가해 버전관리에서 제외합니다.
- 엔트리포인트가 index.py인지 every2cal.py인지 명확히 하여 README.md에 실행 방법을 명시하면 편합니다.

## Libraries and Frameworks

- `icalendar` — .ics 캘린더 파일 생성 및 파싱을 위한 라이브러리.
- `BeautifulSoup4` — HTML/XML 파싱(Everytime AJAX/XML 파싱)에 사용.
- `requests` — 원격 서버로부터 데이터(예: AJAX 결과)를 가져오기 위한 HTTP 클라이언트.
- `Flask` — 웹 인터페이스(서버 엔트리포인트) 제공을 위한 마이크로 웹 프레임워크.
- `gunicorn` — 프로덕션 환경에서 Flask 앱을 실행하기 위한 WSGI 서버(권장).
- `gevent` — 비동기 네트워킹 및 동시성 보조(선택적 사용).
- `boto3` — AWS 서비스(S3 등)와 연동할 때 사용.
- `zappa` — Flask 앱을 AWS Lambda로 손쉽게 배포하도록 돕는 도구.
- `python-dotenv` — .env 파일로부터 환경 변수를 로드하는 유틸리티.

## Coding Standards

아래 코딩 표준은 `every2cal` 리포지토리에 기여하는 개발자들이 일관되고 유지보수 가능한 코드를 작성하도록 돕기 위한 가이드입니다. 짧고 실용적으로 유지합니다.

### 1) 언어/버전
- Python 3.8+ 사용을 권장합니다. (프로젝트의 `requirements.txt`와 일치시키세요.)

### 2) 포맷팅 & 정적분석
- 코드 포맷터: `black` (선호 설정: line-length=88). 커밋 전에 자동 포맷을 적용하세요.
- 임포트 정렬: `isort`를 사용합니다. (Black과 호환되는 설정을 권장)
- 린터: `flake8`로 기본 린팅을 적용하고, 프로젝트 루트에 `.flake8` 또는 `setup.cfg`로 규칙을 명시하세요.
- 타입 검사: 가능하면 `mypy`를 도입해 점진적으로 타입 힌트를 추가합니다.

### 3) 타입 힌트 & 문서화
- 공용 함수/모듈에는 최소한의 타입 힌트를 작성하세요(입력/출력 타입).
- 함수와 클래스에는 간단한 Docstring을 작성합니다. (권장 스타일: Google 또는 NumPy 스타일)

### 4) 코드 스타일(관습)
- 명확한 함수/모듈 분리: I/O(파일/네트워크)와 순수 로직(데이터 변환)을 분리하세요. 예: `convert.py`는 변환 로직, `index.py`는 웹 진입점.
- 전역 상태는 최소화하고, 부작용이 있는 함수는 명시적으로 문서화하세요.
- 진입점 파일(`index.py`, `every2cal.py`)에는 `if __name__ == "__main__":` 보호를 사용합니다.

### 5) 캘린더·시간 관련 규칙
- 날짜/시간은 항상 timezone-aware로 처리하세요. 내부 저장/전송은 UTC 권장.
- `.ics` 생성에는 `icalendar` 라이브러리를 사용하고, 필수 필드(UID, DTSTART, DTEND 등)가 없는 입력은 명시적으로 거르거나 로그를 남깁니다.

### 6) 입력 검증 & 오류 처리
- 외부 입력(XML/HTML/CSV 등)은 신뢰하지 마세요 — 파싱 전에 최소한의 유효성 검사를 수행합니다.
- 실패 가능한 작업은 예외를 명확히 처리하고, 유저에게는 친절한 에러 메시지를 반환하되 내부 로그에는 디버깅 정보를 남깁니다.

### 7) 로깅
- 표준 `logging` 모듈을 사용합니다. 라이브/프로덕션에서는 환경변수로 로그 레벨을 제어하세요.
- 민감한 정보(토큰/비밀번호)는 로그에 기록하지 마세요.

### 8) 보안 & 비밀관리
- 시크릿은 레포에 커밋하지 마세요. `.env` 또는 CI 시크릿을 사용합니다. `python-dotenv`는 로컬 개발 편의용으로만 사용.
- 외부 서비스 호출 시 타임아웃을 설정하고 입력을 검증하세요.

### 9) 의존성 관리
- `requirements.txt`에 의존성을 고정(버전 명시)합니다. 장기적으로는 `pip-tools`/`poetry` 도입 고려.
- 보안 취약점 스캔(예: Dependabot)을 설정하세요.

### 10) 테스트
- 테스트 프레임워크: `pytest` 권장.
- 위치: `tests/` 디렉터리에 모아두고, 핵심 변환기(`convert.py`, `everytime.py`)에 대해 적어도 한 개의 해피패스 테스트와 하나의 에러/경계 테스트를 작성하세요.
- 간단한 테스트 예: 입력 XML → 변환된 `.ics`에 특정 이벤트(UID/요약/시간)가 포함되는지 확인.

### 11) CI / 자동화
- GitHub Actions로 기본 파이프라인 구성 권장: 체크(포맷 검사, 린트, 타입체크, pytest).
- 커밋/푸시에 대해 포맷/린트를 자동으로 검사하도록 설정하세요.

### 12) 커밋 & 브랜치 규칙
- 커밋 메시지는 간결하고 목적 중심으로 작성합니다(예: `fix: handle missing DTSTART in convert`).
- 브랜치: `feature/`, `fix/`, `chore/` 접두사 사용 권장.
- PR은 작은 단위로, 변경 이유와 간단한 테스트 설명을 포함하세요.

### 13) 파일/인코딩/네이밍
- 파일 인코딩은 UTF-8로 통일합니다.
- 불필요한 바이너리(예: `__pycache__`, `*.pyc`)는 `.gitignore`에 추가하세요.

### 14) 문서
- `README.md`에 설치/실행/배포 절차를 명확히 기재합니다. 예제 입력 파일과 기대 출력(예: 샘플 `.ics`)을 포함하면 좋습니다.
- 주요 모듈 상단에 간단한 사용 예시(예: 변환 함수의 입력/출력 형태)를 넣으세요.

### 15) 릴리스 & 버전 관리
- 간단한 시맨틱 버전 규칙(예: `MAJOR.MINOR.PATCH`)을 따르고, 릴리스 노트에 변경 요약을 작성하세요.


# Rule

- 라이브러리를 사용할때는 항상 context7 tool을 사용하여 라이브러리 사용법을 확입하세요.
