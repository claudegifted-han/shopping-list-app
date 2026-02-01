# DJSHS AI Agent System - Scripts

운영 및 관리 스크립트 모음입니다.

## 스크립트 목록

### 1. setup_notion_databases.py
Notion 데이터베이스 자동 생성 스크립트

```bash
# 연결 테스트
python setup_notion_databases.py --test-only

# 데이터베이스 생성
python setup_notion_databases.py \
  --api-key YOUR_NOTION_API_KEY \
  --parent-page YOUR_PAGE_ID

# 환경변수 사용
export NOTION_API_KEY=secret_xxx
export NOTION_PARENT_PAGE=xxx
python setup_notion_databases.py
```

생성되는 데이터베이스:
- 학생 명부 (students)
- 교직원 명부 (teachers)
- 자율연구 현황 (research)
- 학사일정 (events)
- 회의록 (meetings)
- 공문/문서 (documents)
- 동아리 (clubs)

### 2. deployment_validator.py
배포 전 환경 검증 스크립트

```bash
# 전체 검증
python deployment_validator.py --full

# 환경변수만 검증
python deployment_validator.py --env-only

# 파일 구조만 검증
python deployment_validator.py --files-only

# 결과 JSON 내보내기
python deployment_validator.py --full --export report.json
```

검증 항목:
- 환경 변수 설정
- 디렉토리 구조
- 에이전트 파일
- 설정 파일 문법
- 도구 파일 문법
- 보안 설정

### 3. generate_report.py
사용 통계 리포트 생성기

```bash
# 일일 리포트
python generate_report.py --daily

# 주간 리포트
python generate_report.py --weekly

# 월간 리포트
python generate_report.py --monthly

# HTML 형식으로 출력
python generate_report.py --weekly --format html --output report.html
```

### 4. pilot_test.py
파일럿 테스트 도구

```bash
# 시나리오 목록 확인
python pilot_test.py --list

# 빠른 테스트 (5개 시나리오)
python pilot_test.py --quick

# 전체 테스트
python pilot_test.py --full

# 특정 에이전트 테스트
python pilot_test.py --agent academic_affairs
```

## 의존성

```bash
pip install requests pyyaml
```

## 환경 변수

| 변수명 | 설명 | 필수 |
|--------|------|------|
| NOTION_API_KEY | Notion Integration 토큰 | O |
| NOTION_PARENT_PAGE | 데이터베이스 생성 위치 | O |
| NOTION_DB_* | 각 데이터베이스 ID | △ |
| GITHUB_TOKEN | GitHub 연동 토큰 | X |

## 문의

- 시스템: 교육정보부 (042-863-7810)
