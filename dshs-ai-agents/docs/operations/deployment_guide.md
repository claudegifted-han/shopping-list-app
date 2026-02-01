# DSHS AI 에이전트 시스템 배포 가이드

## 배포 개요

| 항목 | 내용 |
|------|------|
| 시스템 | DSHS AI 교무행정 에이전트 시스템 |
| 버전 | 3.0 (Phase 3 Complete) |
| 대상 | 전 교직원 |
| 배포 방식 | 단계적 배포 |

---

## 1. 배포 전 준비

### 1.1 시스템 요구사항

**교직원 PC 요구사항:**

| 항목 | 최소 사양 | 권장 사양 |
|------|----------|----------|
| OS | Windows 10 / macOS 10.15 | Windows 11 / macOS 12 |
| RAM | 8GB | 16GB |
| 저장공간 | 1GB | 5GB |
| 네트워크 | 인터넷 연결 | 고속 인터넷 |

**필수 소프트웨어:**

```
□ Node.js 18 이상
□ Git
□ Claude Code CLI
□ 터미널 (Terminal / PowerShell)
```

### 1.2 사전 설치

**1. Node.js 설치**

```bash
# macOS (Homebrew)
brew install node

# Windows (공식 설치 프로그램)
# https://nodejs.org 에서 LTS 버전 다운로드
```

**2. Claude Code 설치**

```bash
# npm을 통한 설치
npm install -g @anthropic/claude-code

# 설치 확인
claude --version
```

**3. Git 설치**

```bash
# macOS
brew install git

# Windows
# https://git-scm.com 에서 다운로드
```

### 1.3 Notion 준비

```
□ Notion 워크스페이스 생성 완료
□ Integration 생성 및 토큰 발급
□ 7개 데이터베이스 생성 완료
□ Integration 연결 완료
□ 초기 데이터 입력 완료
```

---

## 2. 배포 단계

### 2.1 단계별 배포 계획

| 단계 | 대상 | 기간 | 목표 |
|------|------|------|------|
| 1단계 | IT 담당자 | 1주 | 시스템 검증 |
| 2단계 | 부장교사 | 1주 | 기능 검증 |
| 3단계 | 전 교직원 | 2주 | 전체 배포 |

### 2.2 1단계: IT 담당자 배포

**대상:** 교육정보부 담당자 (2~3명)

**목표:**
- 시스템 설치 및 설정 검증
- 문제점 사전 발견 및 해결
- 배포 스크립트 검증

**절차:**

```bash
# 1. 프로젝트 클론
git clone [repository-url] dshs-ai-agents
cd dshs-ai-agents

# 2. 환경 설정
cp .env.example .env
# .env 파일에 API 키 설정

# 3. Claude Code MCP 설정
mkdir -p ~/.claude
cp config/claude-settings.json ~/.claude/settings.json

# 4. 테스트 실행
claude
@교무운영부 시스템 테스트 - 오늘 날짜 알려줘
```

**검증 항목:**

```
□ Claude Code 정상 실행
□ MCP 연결 정상
□ 에이전트 응답 정상
□ Notion 연동 정상
```

### 2.3 2단계: 부장교사 배포

**대상:** 각 부서 부장교사 (16명)

**목표:**
- 실제 업무 적용 가능성 검증
- 부서별 요구사항 수집
- 사용자 피드백 수집

**절차:**

1. **설치 세션** (1시간)
   - IT 담당자가 직접 설치 지원
   - 개별 PC에 환경 설정

2. **교육 세션** (2시간)
   - 시스템 사용법 교육
   - 담당 부서 에이전트 집중 교육

3. **시범 사용** (1주)
   - 실제 업무에 적용
   - 피드백 수집

**피드백 양식:**

```
부서:
사용자:
날짜:

1. 사용한 에이전트:
2. 요청 내용:
3. 응답 품질 (1-5):
4. 개선 필요 사항:
5. 기타 의견:
```

### 2.4 3단계: 전체 배포

**대상:** 전 교직원

**절차:**

1. **배포 공지** (D-7)
   - 교무회의 안내
   - 이메일 공지
   - 설치 가이드 배포

2. **자율 설치 기간** (D-Day ~ D+7)
   - 자율 설치 및 설정
   - IT 담당자 상시 지원

3. **집합 교육** (D+3, D+5)
   - 컴퓨터실 교육 세션
   - 2시간 × 2회

4. **지원 기간** (D+7 ~ D+14)
   - 개별 문의 대응
   - 추가 교육 필요시 진행

---

## 3. 설치 스크립트

### 3.1 자동 설치 스크립트 (macOS/Linux)

`scripts/install.sh`:

```bash
#!/bin/bash

echo "=== DSHS AI 에이전트 시스템 설치 ==="

# Node.js 확인
if ! command -v node &> /dev/null; then
    echo "Node.js가 설치되어 있지 않습니다. 먼저 설치해주세요."
    exit 1
fi

# Claude Code 설치
echo "Claude Code 설치 중..."
npm install -g @anthropic/claude-code

# 프로젝트 클론
echo "프로젝트 다운로드 중..."
git clone [repository-url] ~/dshs-ai-agents
cd ~/dshs-ai-agents

# 환경 설정
echo "환경 설정 중..."
mkdir -p ~/.claude
cp config/claude-settings.json ~/.claude/settings.json

echo "=== 설치 완료 ==="
echo "1. ~/.claude/settings.json에서 NOTION_API_KEY를 설정하세요"
echo "2. 터미널에서 'claude' 명령으로 시작하세요"
```

### 3.2 Windows 설치 스크립트

`scripts/install.ps1`:

```powershell
Write-Host "=== DSHS AI 에이전트 시스템 설치 ===" -ForegroundColor Green

# Node.js 확인
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js가 설치되어 있지 않습니다. 먼저 설치해주세요." -ForegroundColor Red
    exit 1
}

# Claude Code 설치
Write-Host "Claude Code 설치 중..."
npm install -g @anthropic/claude-code

# 프로젝트 클론
Write-Host "프로젝트 다운로드 중..."
git clone [repository-url] $HOME\dshs-ai-agents
Set-Location $HOME\dshs-ai-agents

# 환경 설정
Write-Host "환경 설정 중..."
New-Item -ItemType Directory -Force -Path $HOME\.claude
Copy-Item config\claude-settings.json $HOME\.claude\settings.json

Write-Host "=== 설치 완료 ===" -ForegroundColor Green
Write-Host "1. $HOME\.claude\settings.json에서 NOTION_API_KEY를 설정하세요"
Write-Host "2. 터미널에서 'claude' 명령으로 시작하세요"
```

---

## 4. 교육 자료 배포

### 4.1 배포 자료 목록

| 자료 | 형식 | 배포 방법 |
|------|------|----------|
| 사용자 가이드 | PDF | 이메일 첨부 |
| 빠른 참조 카드 | PDF (1페이지) | 인쇄 배포 |
| 설치 가이드 | PDF | 이메일 첨부 |
| 교육 슬라이드 | PPT | 집합 교육 |

### 4.2 인쇄물 배포

**빠른 참조 카드:**
- A4 1페이지 양면
- 코팅 처리
- 교직원 1인당 1부

---

## 5. 배포 후 지원

### 5.1 지원 채널

| 채널 | 용도 | 운영 시간 |
|------|------|----------|
| 헬프데스크 | 기술 문제 | 평일 09:00-17:00 |
| 이메일 | 일반 문의 | 24시간 (익일 답변) |
| FAQ | 자주 묻는 질문 | 상시 |

### 5.2 FAQ 페이지

```
Q. 에이전트가 응답하지 않습니다.
A. 1) 인터넷 연결 확인
   2) Claude Code 재시작
   3) 교육정보부 문의

Q. Notion 연동이 안 됩니다.
A. 1) API 키 설정 확인
   2) settings.json 확인
   3) 교육정보부 문의

Q. 원하는 형식으로 출력되지 않습니다.
A. 1) 요청을 더 구체적으로 작성
   2) 형식 예시를 함께 제공
   3) 교육연구부 피드백 접수
```

### 5.3 피드백 수집

**주간 피드백 집계:**
- 총 문의 건수
- 문제 유형별 분류
- 해결률
- 개선 필요 사항

---

## 6. 롤백 계획

### 6.1 롤백 조건

```
- 전체 시스템 장애 발생
- 심각한 보안 문제 발견
- 사용자 70% 이상 문제 보고
```

### 6.2 롤백 절차

```bash
# 1. 문제 공지
# - 전 교직원 이메일 발송
# - 시스템 일시 중단 안내

# 2. 이전 버전 복구
git checkout [previous-stable-version]

# 3. 설정 복구
cp backup/settings.json ~/.claude/settings.json

# 4. 정상화 확인
claude --version
@교무운영부 시스템 테스트

# 5. 재배포 공지
```

---

## 7. 체크리스트

### 배포 전

```
□ 시스템 요구사항 확인
□ 필수 소프트웨어 설치 가이드 준비
□ Notion 설정 완료
□ 설치 스크립트 테스트
□ 교육 자료 준비
□ 지원 체계 구축
```

### 배포 중

```
□ 1단계 (IT 담당자) 완료
□ 2단계 (부장교사) 완료
□ 전체 공지 발송
□ 설치 지원 진행
□ 집합 교육 진행
```

### 배포 후

```
□ 설치율 확인 (목표: 90% 이상)
□ 피드백 수집
□ 문제 해결
□ 추가 교육 진행 (필요시)
□ 안정화 확인
```

---

## 8. 연락처

| 구분 | 담당 | 연락처 |
|------|------|--------|
| 배포 총괄 | 교육정보부장 | 042-863-7810 |
| 기술 지원 | 시스템 관리자 | 내선 101 |
| 교육 문의 | 교육연구부 | 042-863-7815 |
| 긴급 연락 | IT 담당자 | 010-XXXX-XXXX |

---

**문서 버전:** 1.0
**작성일:** 2026-02-01
**작성:** 교육정보부
