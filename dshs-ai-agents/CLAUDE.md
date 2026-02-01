# DSHS AI Administrative Agent System

## 프로젝트 개요
대전과학고등학교 교무 행정 AI 에이전트 시스템.
16개 부서 부장 에이전트와 특수 에이전트로 구성된 "1인 교무실" 시스템.

**버전**: 6.0 (Phase 6 Complete - 확장 기능)
**업데이트**: 2026-02-01

## 핵심 규칙
1. 모든 에이전트는 대전과학고 학칙과 영재학교 규정을 준수한다
2. 학생 개인정보는 절대 외부로 유출하지 않는다
3. 의사결정 권한이 필요한 사항은 반드시 사용자(교사)에게 확인한다
4. NEIS 기재 시 교육부 기재요령을 따른다
5. 부서 간 협업이 필요한 사항은 관련 에이전트를 함께 호출한다

## 에이전트 호출 방법
```bash
# 단일 에이전트
@교무운영부 인사자문위원회 회의록 작성해줘
@영재교육부 기초 자율연구 팀 조직 현황 정리해줘
@교육평가부 1학기 중간고사 성적 분포 분석해줘

# 다중 에이전트 (브레인스토밍)
@브레인스토밍 새 학기 시간표 편성 관련 의견 수렴해줘
@브레인스토밍 기숙사 외출 규정 변경에 대해 분석해줘

# CEO 모드 (전체 조율)
@전략기획실 올해 학교교육계획 초안 작성해줘
@전략기획실 신학년 준비 현황 전 부서 점검해줘
```

## 배포된 에이전트 (20개)

### CEO 전략기획실
- [x] **ceo_strategy** - 전체 에이전트 오케스트레이션, 전략 자문

### 교학 운영 그룹 (5개)
- [x] **academic_affairs** (교무운영부) - 학교 행정, 인사, 복무, 규정 관리
- [x] **curriculum** (교육과정부) - 교육과정, 학사관리, 시간표
- [x] **evaluation** (교육평가부) - 학업성적관리, 평가, 성적 분석
- [x] **research** (교육연구부) - 수업 혁신, 교원 연수, 도서관
- [x] **edtech** (교육정보부) - IT 인프라, 정보보안, 시스템

### 학생 지원 그룹 (7개)
- [x] **student_life** (학생생활안전부) - 생활지도, 상담, 보건, 안전
- [x] **afterschool** (방과후인성부) - 방과후학교, 동아리, 축제
- [x] **career** (진로진학부) - 진로/진학 상담, 대학 정보
- [x] **dormitory** (사감부) - 기숙사 운영, 야간자율학습
- [x] **grade_1** (1학년부) - 1학년 관리, 국외탐구, 기초연구
- [x] **grade_2** (2학년부) - 2학년 관리, 심화연구, 대회 참가
- [x] **grade_3** (3학년부) - 3학년 관리, 졸업논문, 대입 진학

### 연구·입학 그룹 (4개)
- [x] **science_edu** (과학교육부) - 실험실, 현장연구, 과학대회
- [x] **gifted_edu** (영재교육부) - 자율연구, 졸업논문, R&E
- [x] **international** (국제교류부) - 국제교류, 영어교육, 번역
- [x] **admission** (입학지원부) - 입학전형, 홍보, 원서접수

### 특수 에이전트 (1개)
- [x] **brainstorm** (다부서 협의) - 정책 시뮬레이션, 기획회의 대체

### 외부 서비스 에이전트 (3개) - Phase 6 추가
- [x] **parent_support** (학부모지원) - 학부모 문의 응대, 학교 정보 안내
- [x] **faq_bot** (FAQ) - 자주 묻는 질문 자동 응답
- [x] **freshman_guide** (신입생안내) - 신입생 맞춤형 안내, 적응 가이드

## 데이터 소스
- **Notion**: 학교 업무 데이터베이스 (MCP 연동)
- **로컬 파일**: 규정집, 교육과정, 학사일정
- **템플릿**: 공문, 보고서, NEIS 기재 양식

## 보안 규칙
| 데이터 유형 | 보안 등급 | 접근 가능 에이전트 |
|------------|----------|------------------|
| 학생 성적 | 최고기밀 | evaluation |
| 입학전형 | 최고기밀 | admission |
| 상담 기록 | 최고기밀 | student_life |
| 교원 인사 | 기밀 | academic_affairs |
| 일반 학사 | 일반 | 전체 |

## 디렉토리 구조
```
dshs-ai-agents/
├── CLAUDE.md                    # 프로젝트 설명 (이 파일)
├── agents/                      # 에이전트 역할 정의 (17개)
├── prompts/system/              # 시스템 프롬프트 (16개)
├── config/
│   ├── agents.yaml              # 전체 에이전트 설정
│   ├── workflows.yaml           # 워크플로우 정의 (5개)
│   └── mcp.json                 # MCP 서버 설정
├── templates/
│   ├── reports/                 # 보고서 템플릿 (9개)
│   ├── letters/                 # 공문/가정통신문 템플릿 (3개)
│   └── neis/                    # NEIS 기재 템플릿 (1개)
├── tools/                       # 커스텀 도구 (9개)
│   ├── notion_tools.py          # Notion MCP 연동
│   ├── doc_generator.py         # 문서 생성기
│   ├── schedule_tools.py        # 일정 관리
│   ├── neis_helper.py           # NEIS 기재 지원
│   ├── statistics_tools.py      # 통계 분석
│   ├── monitoring.py            # 모니터링 및 로깅
│   ├── feedback_system.py       # 피드백 수집 (Phase 6)
│   ├── external_integrations.py # 외부 연동 (Phase 6)
│   └── advanced_analytics.py    # 고급 분석 (Phase 6)
├── scripts/                     # 운영 스크립트 (4개)
│   ├── setup_notion_databases.py # Notion DB 자동 생성
│   ├── deployment_validator.py   # 배포 검증
│   ├── generate_report.py        # 리포트 생성
│   └── pilot_test.py             # 파일럿 테스트
├── data/
│   ├── regulations/             # 규정집 (학칙, 연구지침)
│   └── calendars/               # 학사일정 (2026학년도)
├── tests/scenarios/             # 테스트 시나리오 및 결과
│   ├── test_scenarios.md        # 13개 테스트 시나리오
│   └── test_results.md          # 테스트 결과 보고서
└── docs/                        # 문서
    ├── user_guide.md            # 상세 사용 가이드
    ├── quick_reference.md       # 빠른 참조 카드
    ├── setup/                   # 설정 가이드
    │   ├── notion_setup_guide.md    # Notion 설정 가이드
    │   └── mcp_configuration.md     # MCP 설정 가이드
    ├── training/                # 교육 자료
    │   └── teacher_training_guide.md # 교직원 교육 자료
    └── operations/              # 운영 매뉴얼
        ├── operations_manual.md     # 운영 매뉴얼
        ├── prompt_tuning_guide.md   # 프롬프트 튜닝 가이드
        └── deployment_guide.md      # 배포 가이드
```

## 효율화 목표 (Phase 3에서 측정)
| 업무 | Before | After | 효율화 |
|------|--------|-------|--------|
| 공문 작성 | 30분 | 5분 | 83% ↓ |
| 회의록 정리 | 1시간 | 10분 | 83% ↓ |
| 다부서 협의 | 2시간 회의 | 10분 시뮬레이션 | 92% ↓ |
| 사업 계획서 | 2주 | 2일 | 86% ↓ |
| 연수 자료 | 1일 | 2시간 | 75% ↓ |

## Phase 3 완료 (2026-02-01)
- [x] 실제 업무 시나리오 테스트 (tests/scenarios/)
- [x] 커스텀 도구 구현 (tools/)
- [x] Notion MCP 연동 설정 (config/mcp.json)
- [x] 교직원 사용 가이드 작성 (docs/)
- [x] 규정집 및 학사일정 데이터 (data/)

## Phase 4 완료 (2026-02-01) - 운영 준비
- [x] 테스트 시나리오 실행 및 결과 분석 (13/13 PASS)
- [x] Notion 데이터베이스 설정 가이드 작성
- [x] MCP 설정 가이드 작성
- [x] 교직원 교육 자료 개발 (2시간 교육 과정)
- [x] 운영 매뉴얼 작성 (일일/주간/월간 운영)
- [x] 프롬프트 튜닝 가이드 작성
- [x] 단계별 배포 가이드 작성

## 배포 계획
| 단계 | 대상 | 기간 | 목표 |
|------|------|------|------|
| 1단계 | IT 담당자 | 1주 | 시스템 검증 |
| 2단계 | 부장교사 | 1주 | 기능 검증 |
| 3단계 | 전 교직원 | 2주 | 전체 배포 |

## Phase 5 완료 (2026-02-01) - 실제 운영 준비
- [x] Notion 데이터베이스 자동 생성 스크립트 (scripts/setup_notion_databases.py)
- [x] 배포 환경 검증 도구 (scripts/deployment_validator.py)
- [x] 모니터링 및 로깅 시스템 (tools/monitoring.py)
- [x] 사용 통계 리포트 생성기 (scripts/generate_report.py)
- [x] 파일럿 테스트 도구 (scripts/pilot_test.py)

## 실제 배포 체크리스트
```
Phase 5-1: IT 담당자 파일럿 (1주)
□ Notion 워크스페이스 생성 (notion.so)
□ scripts/setup_notion_databases.py 실행
□ .env 파일 설정 (API 키, DB ID)
□ scripts/deployment_validator.py --full 실행
□ MCP 서버 설정 확인
□ scripts/pilot_test.py --quick 실행

Phase 5-2: 부장교사 테스트 (1주)
□ scripts/pilot_test.py --full 실행
□ 피드백 수집 및 프롬프트 튜닝
□ 운영 매뉴얼 검토

Phase 5-3: 전교직원 배포 (2주)
□ 교직원 교육 (docs/training/teacher_training_guide.md)
□ 모니터링 대시보드 운영 (tools/monitoring.py --dashboard)
□ 주간 리포트 생성 (scripts/generate_report.py --weekly)
```

## Phase 6 완료 (2026-02-01) - 확장 기능
- [x] 피드백 수집 시스템 (tools/feedback_system.py)
- [x] 추가 에이전트 3개 (학부모지원, FAQ, 신입생안내)
- [x] 외부 시스템 연동 (tools/external_integrations.py)
  - Google Calendar 연동 준비
  - 이메일 알림 시스템
  - NEIS 연동 준비
- [x] 고급 분석 및 예측 (tools/advanced_analytics.py)
  - 트렌드 분석
  - 이상 징후 탐지
  - 사용량 예측
  - 자동 인사이트 생성
- [x] FAQ 데이터베이스 (data/faq/school_faq.json)
- [x] 신입생 체크리스트 (data/freshman/checklist.json)

## 다음 단계 (Phase 7 - 고도화)
- [ ] 실제 Google Calendar API 연동
- [ ] SMTP 이메일 발송 연동
- [ ] NEIS Open API 연동
- [ ] 음성 인터페이스 추가 (선택)
- [ ] 모바일 앱 연동 (선택)
