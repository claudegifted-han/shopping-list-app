# Notion 데이터베이스 설정 가이드

## 개요

DJSHS AI 에이전트 시스템과 Notion을 연동하기 위한 데이터베이스 설정 가이드입니다.

---

## 1. Notion 워크스페이스 설정

### 1.1 워크스페이스 생성

1. [Notion](https://notion.so) 접속
2. 학교 계정으로 워크스페이스 생성
3. 워크스페이스 이름: `대전과학고 교무행정`

### 1.2 Integration 생성

1. [Notion Developers](https://developers.notion.com) 접속
2. `New integration` 클릭
3. 설정:
   - Name: `DJSHS AI Agent System`
   - Associated workspace: `대전과학고 교무행정`
   - Capabilities: Read content, Update content, Insert content
4. `Submit` 후 **Internal Integration Token** 복사
5. 토큰을 안전하게 보관 (환경변수로 사용)

---

## 2. 데이터베이스 생성

### 2.1 필수 데이터베이스 (7개)

아래 데이터베이스를 Notion에 생성합니다.

#### 📊 학생 명부 (students)

| 속성명 | 타입 | 설명 |
|--------|------|------|
| 이름 | Title | 학생 이름 |
| 학번 | Text | 학번 (예: 20261001) |
| 학년 | Select | 1학년, 2학년, 3학년 |
| 반 | Select | 1반, 2반, 3반 |
| 번호 | Number | 출석번호 |
| 담임 | Relation | 교직원 명부 연결 |
| 상태 | Select | 재학, 휴학, 졸업 |

```
보안등급: 🟠 High
접근 에이전트: academic_affairs, grade_1, grade_2, grade_3
```

#### 👨‍🏫 교직원 명부 (teachers)

| 속성명 | 타입 | 설명 |
|--------|------|------|
| 이름 | Title | 교직원 이름 |
| 직위 | Select | 교장, 교감, 부장, 교사, 직원 |
| 부서 | Select | 교무운영부, 영재교육부 등 |
| 담당과목 | Multi-select | 수학, 물리, 화학 등 |
| 이메일 | Email | 학교 이메일 |
| 내선번호 | Text | 내선번호 |

```
보안등급: 🟠 High
접근 에이전트: academic_affairs, ceo_strategy
```

#### 🔬 자율연구 현황 (research)

| 속성명 | 타입 | 설명 |
|--------|------|------|
| 연구제목 | Title | 연구 제목 |
| 연구유형 | Select | 기초연구, 심화연구, 졸업논문 |
| 학년 | Select | 1학년, 2학년, 3학년 |
| 연구자 | Relation | 학생 명부 연결 |
| 지도교사 | Relation | 교직원 명부 연결 |
| 분야 | Select | 수학, 물리, 화학, 생물, 지구과학, 정보과학, 융합 |
| 상태 | Select | 계획중, 진행중, 완료, 보류 |
| 시작일 | Date | 연구 시작일 |
| 종료일 | Date | 연구 종료일 |
| 예산 | Number | 연구비 (원) |

```
보안등급: 🟢 Standard
접근 에이전트: gifted_edu, science_edu, grade_1, grade_2, grade_3
```

#### 📅 학사일정 (events)

| 속성명 | 타입 | 설명 |
|--------|------|------|
| 일정명 | Title | 일정 이름 |
| 유형 | Select | 시험, 행사, 연구, 방학, 회의 |
| 시작일 | Date | 시작 날짜 |
| 종료일 | Date | 종료 날짜 |
| 담당부서 | Multi-select | 담당 부서 |
| 대상 | Multi-select | 1학년, 2학년, 3학년, 전교생, 교직원 |
| 장소 | Text | 행사 장소 |
| 설명 | Text | 상세 설명 |

```
보안등급: 🟢 Standard
접근 에이전트: 전체
```

#### 📝 회의록 (meetings)

| 속성명 | 타입 | 설명 |
|--------|------|------|
| 회의명 | Title | 회의 이름 |
| 일시 | Date | 회의 일시 |
| 장소 | Text | 회의 장소 |
| 참석자 | Relation | 교직원 명부 연결 |
| 부서 | Select | 담당 부서 |
| 안건 | Text | 회의 안건 |
| 결정사항 | Text | 의결 사항 |
| 후속조치 | Text | 후속 조치 사항 |

```
보안등급: 🟢 Standard
접근 에이전트: academic_affairs, ceo_strategy
```

#### 📄 공문/문서 (documents)

| 속성명 | 타입 | 설명 |
|--------|------|------|
| 제목 | Title | 문서 제목 |
| 문서번호 | Text | 문서번호 |
| 유형 | Select | 공문, 가정통신문, 보고서, 계획서 |
| 작성부서 | Select | 작성 부서 |
| 작성일 | Date | 작성일 |
| 상태 | Select | 초안, 검토중, 완료, 발송완료 |
| 내용 | Text | 문서 내용 요약 |
| 첨부파일 | Files | 첨부 파일 |

```
보안등급: 🟢 Standard
접근 에이전트: academic_affairs, 각 부서
```

#### 🎭 동아리 (clubs)

| 속성명 | 타입 | 설명 |
|--------|------|------|
| 동아리명 | Title | 동아리 이름 |
| 분류 | Select | 학술, 체육, 예술, 봉사, 기타 |
| 지도교사 | Relation | 교직원 명부 연결 |
| 부장 | Relation | 학생 명부 연결 |
| 인원 | Number | 부원 수 |
| 활동요일 | Multi-select | 월, 화, 수, 목, 금 |
| 활동장소 | Text | 활동 장소 |
| 상태 | Select | 활동중, 휴면, 해체 |

```
보안등급: 🟢 Standard
접근 에이전트: afterschool
```

### 2.2 보안 데이터베이스 (3개) - 별도 관리

⚠️ 아래 데이터베이스는 최고 보안 등급으로 AI 시스템 직접 연동하지 않음

| 데이터베이스 | 설명 | 관리 |
|--------------|------|------|
| 성적 (grades) | 학생 성적 정보 | NEIS 직접 관리 |
| 입학전형 (admission) | 전형 정보 | 입학지원부 오프라인 관리 |
| 상담기록 (counseling) | 상담 내용 | 상담실 별도 시스템 |

---

## 3. 데이터베이스 공유 설정

### 3.1 Integration 연결

각 데이터베이스에 Integration을 연결합니다:

1. 데이터베이스 페이지 열기
2. 우측 상단 `···` 클릭
3. `Add connections` 선택
4. `DJSHS AI Agent System` 선택
5. `Confirm` 클릭

### 3.2 데이터베이스 ID 확인

각 데이터베이스의 ID를 확인하여 설정 파일에 입력합니다:

1. 데이터베이스 페이지 URL 확인
2. URL 형식: `https://notion.so/workspace/DATABASE_ID?v=...`
3. `DATABASE_ID` 부분 (32자리 문자열) 복사

---

## 4. 환경 변수 설정

### 4.1 .env 파일 생성

프로젝트 루트에 `.env` 파일 생성:

```bash
# Notion API
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Database IDs
NOTION_DB_STUDENTS=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_TEACHERS=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_RESEARCH=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_EVENTS=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_MEETINGS=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_DOCUMENTS=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_CLUBS=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 4.2 보안 주의사항

```
⚠️ 중요: .env 파일은 절대 Git에 커밋하지 마세요!
```

`.gitignore`에 추가:
```
.env
.env.local
.env.*.local
```

---

## 5. MCP 서버 설정

### 5.1 Claude Code 설정

`~/.claude/settings.json`에 MCP 서버 추가:

```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": {
        "NOTION_API_KEY": "${NOTION_API_KEY}"
      }
    }
  }
}
```

### 5.2 연결 테스트

Claude Code에서 테스트:

```
Notion 학사일정 데이터베이스에서 이번 달 일정 조회해줘
```

---

## 6. 초기 데이터 입력

### 6.1 필수 초기 데이터

| 데이터베이스 | 초기 데이터 |
|--------------|------------|
| 학사일정 | 2026학년도 학사일정 (data/calendars/ 참조) |
| 교직원 | 부서별 교직원 정보 |
| 동아리 | 현재 운영 동아리 목록 |

### 6.2 데이터 입력 방법

1. **수동 입력**: Notion UI에서 직접 입력
2. **CSV 가져오기**: Notion의 Import 기능 사용
3. **API 활용**: 스크립트를 통한 대량 입력

---

## 7. 체크리스트

```
□ Notion 워크스페이스 생성
□ Integration 생성 및 토큰 발급
□ 7개 데이터베이스 생성
□ 각 데이터베이스에 Integration 연결
□ 데이터베이스 ID 확인
□ .env 파일 설정
□ .gitignore에 .env 추가
□ MCP 서버 설정
□ 연결 테스트
□ 초기 데이터 입력
```

---

## 문의

- 시스템 설정: 교육정보부 (042-863-7810)
- Notion 운영: 교무운영부 (042-863-7801)
