# MCP (Model Context Protocol) 설정 가이드

## 개요

DSHS AI 에이전트 시스템에서 Notion과 외부 도구를 연동하기 위한 MCP 설정 가이드입니다.

---

## 1. MCP 개념 이해

### 1.1 MCP란?

MCP(Model Context Protocol)는 AI 모델이 외부 도구 및 데이터 소스와 상호작용할 수 있게 해주는 프로토콜입니다.

```
┌─────────────┐     MCP      ┌─────────────┐
│  Claude AI  │ ◄──────────► │  MCP Server │
│  (에이전트)  │              │  (Notion 등) │
└─────────────┘              └─────────────┘
```

### 1.2 DSHS 시스템의 MCP 구성

| MCP 서버 | 용도 | 상태 |
|----------|------|------|
| Notion | 학교 데이터베이스 연동 | 필수 |
| GitHub | 코드/문서 저장소 | 선택 |
| Filesystem | 로컬 파일 접근 | 선택 |

---

## 2. Claude Code MCP 설정

### 2.1 설정 파일 위치

```bash
# macOS / Linux
~/.claude/settings.json

# Windows
%USERPROFILE%\.claude\settings.json
```

### 2.2 기본 설정 구조

```json
{
  "mcpServers": {
    "서버이름": {
      "command": "실행 명령",
      "args": ["인자1", "인자2"],
      "env": {
        "환경변수": "값"
      }
    }
  }
}
```

---

## 3. Notion MCP 서버 설정

### 3.1 Notion MCP 서버 설치

```bash
# npm을 통한 설치 (자동)
npx -y @notionhq/notion-mcp-server
```

### 3.2 settings.json 설정

```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": {
        "NOTION_API_KEY": "secret_your_api_key_here"
      }
    }
  }
}
```

### 3.3 환경 변수 방식 (권장)

API 키를 직접 노출하지 않고 환경 변수 사용:

**~/.zshrc 또는 ~/.bashrc:**
```bash
export NOTION_API_KEY="secret_your_api_key_here"
```

**settings.json:**
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

---

## 4. 프로젝트별 MCP 설정

### 4.1 프로젝트 설정 파일

프로젝트 디렉토리에 `.claude/settings.json` 생성:

```
dshs-ai-agents/
├── .claude/
│   └── settings.json    # 프로젝트별 MCP 설정
├── config/
│   └── mcp.json         # MCP 설정 문서 (참조용)
└── ...
```

### 4.2 DSHS 프로젝트 MCP 설정

`.claude/settings.json`:

```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": {
        "NOTION_API_KEY": "${NOTION_API_KEY}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@anthropic/mcp-server-filesystem",
        "./data",
        "./templates"
      ]
    }
  }
}
```

---

## 5. MCP 도구 사용법

### 5.1 Notion 도구

Claude Code에서 사용 가능한 Notion 도구:

| 도구 | 기능 | 예시 |
|------|------|------|
| `mcp__notion__API-post-search` | 검색 | "학사일정 검색해줘" |
| `mcp__notion__API-retrieve-a-page` | 페이지 조회 | "회의록 페이지 열어줘" |
| `mcp__notion__API-post-page` | 페이지 생성 | "새 회의록 만들어줘" |
| `mcp__notion__API-patch-page` | 페이지 수정 | "연구 상태 업데이트해줘" |
| `mcp__notion__API-retrieve-a-database` | DB 정보 | "학생 명부 구조 알려줘" |

### 5.2 사용 예시

```
# 학사일정 조회
@교무운영부 Notion에서 3월 학사일정 조회해줘

# 자율연구 현황 업데이트
@영재교육부 홍길동 학생의 연구 상태를 '진행중'으로 업데이트해줘

# 회의록 생성
@교무운영부 오늘 교무회의 회의록을 Notion에 저장해줘
```

---

## 6. 보안 설정

### 6.1 접근 제어

데이터베이스별 접근 권한 설정:

```json
{
  "securitySettings": {
    "levels": {
      "highest": {
        "databases": ["grades", "admission", "counseling"],
        "agents": ["evaluation", "admission", "student_life"]
      },
      "high": {
        "databases": ["students", "teachers"],
        "agents": ["academic_affairs", "edtech"]
      },
      "standard": {
        "databases": ["research", "events", "meetings", "documents", "clubs"],
        "agents": ["all"]
      }
    }
  }
}
```

### 6.2 감사 로그

MCP 호출 로그 활성화:

```json
{
  "logging": {
    "enabled": true,
    "level": "info",
    "auditLog": true
  }
}
```

---

## 7. 문제 해결

### 7.1 연결 실패

**증상:** MCP 서버 연결 안됨

**해결:**
```bash
# 1. Node.js 버전 확인 (18 이상 필요)
node --version

# 2. npx 캐시 정리
npx clear-npx-cache

# 3. MCP 서버 수동 실행 테스트
NOTION_API_KEY=your_key npx -y @notionhq/notion-mcp-server
```

### 7.2 권한 오류

**증상:** 데이터베이스 접근 거부

**해결:**
1. Notion에서 해당 데이터베이스에 Integration 연결 확인
2. Integration 권한 확인 (Read/Update/Insert)
3. API 키 유효성 확인

### 7.3 타임아웃

**증상:** 요청 시간 초과

**해결:**
```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "timeout": 60000
    }
  }
}
```

---

## 8. 테스트

### 8.1 연결 테스트

Claude Code에서 실행:

```
Notion 연결 상태 확인해줘
```

### 8.2 데이터 조회 테스트

```
Notion 학사일정 데이터베이스에서 최근 일정 3개 조회해줘
```

### 8.3 데이터 생성 테스트

```
Notion 회의록 데이터베이스에 테스트 항목 추가해줘:
- 회의명: MCP 연동 테스트
- 일시: 오늘
- 내용: 테스트 성공
```

---

## 9. 체크리스트

```
□ Node.js 18 이상 설치
□ Notion API 키 발급
□ 환경 변수 설정 (NOTION_API_KEY)
□ settings.json 작성
□ MCP 서버 연결 테스트
□ 데이터베이스 조회 테스트
□ 데이터 생성/수정 테스트
□ 보안 설정 확인
```

---

## 문의

- MCP 설정: 교육정보부 (042-863-7810)
- Notion 연동: 교무운영부 (042-863-7801)
