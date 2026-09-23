# R&E 주제 심사 그래프

R&E 주제 제안서 한 건을 여러 AI 에이전트가 나눠 심사하는 Claude Code 워크플로입니다.
이미 쓰고 있는 교과 R&E 에이전트 6개, 운영 에이전트, 협의회 시뮬레이터를 **그래프**로 이었습니다.
누가 무엇을 받아 누구에게 넘기는지, 어디서 검수하고 어디서 사람이 결재하는지가 정해져 있고,
모든 단계가 **과제 카드**(`card.json`) 한 장에 기록됩니다.

```
제안서 ─▶ 분야 판별 ─┬─▶ 교과 에이전트 (해당 분야 1~3개) ─┐
                    └─▶ 운영 에이전트 (항상) ─────────────┴─▶ 협의회 ─▶ 관문 ─▶ 결재(사람) ─▶ 학생 피드백
                                ▲                                     │
                                └──────── 기준 미달이면 그 노드만 다시 ◀─┘
```

- **동시에**: 교과·운영 검토는 한꺼번에 돌고, 다 끝나면 협의회가 모아서 정리합니다.
- **관문**: 처음 보는 검수 에이전트가 공통 검토 카드 기준으로 심사 결과물을 점검합니다. 미달이면 해당 노드만 다시 돕니다(최대 2번).
- **결재**: 사람만 합니다. 승인 · 조건부 승인 · 재검토 요청 · 반려 · 보류 중에서 고릅니다.
- **이어서 하기**: 중간에 끊겨도 카드에 남은 기록부터 다시 시작합니다.

## 준비물

- Claude Code (WSL Ubuntu 포함), `python3` — 스크립트는 표준 라이브러리만 씁니다.
- 기존 스킬 8개가 `~/.claude/skills/`에 있어야 합니다. Claude Code에서 `/skills`로 확인하세요.

| 노드 | 쓰는 스킬 |
|---|---|
| 수학 · 물리 · 화학 | `math-rne-agent` · `physics-rne-agent` · `chemistry-rne-agent` |
| 생명 · 지구 · 정보 | `biology-rne-agent` · `earth-science-rne-agent` · `cs-rne-agent` |
| 운영 · 협의회 | `rne-operations-agent` · `rne-council-simulator` |

스킬 이름이 다르면 `.claude/agents/rne-review-*.md`의 `skills:` 줄을 고치세요.
스킬이 없으면 에이전트는 대체 기준(`references/fallback-rubric.md`)으로 검토하고, 결재 요약에 그 사실이 표시됩니다.

## 설치

```bash
unzip rne-review-graph.zip -d ~/
cd ~/rne-review-graph
claude
```

한글 파일 이름이 깨져 풀리면 `python3 -m zipfile -e rne-review-graph.zip ~/`로 풀어 주세요.

이 폴더 자체가 프로젝트입니다. 스킬과 에이전트가 `.claude/` 안에 들어 있어 따로 설치할 것이 없습니다.
다른 프로젝트에서도 쓰려면 `.claude/skills/rne-review-graph/`와 `.claude/agents/*.md`를 `~/.claude/` 아래 같은 위치로 복사하세요.

## 예시 제안서로 써 보기

```
/rne-review-graph rne-review/proposals/예시_물03_제안서.md 물03
```

분야 판별(물리·정보) → 물리·정보·운영 동시 검토 → 협의회 → 관문 → 결재 질문 → 학생 피드백 순서로 진행됩니다.
결재 단계에서 요약이 나오면 고르기만 하면 됩니다. 보류하려면 '기타'에 "보류"라고 적으세요.
이 예시로 미리 돌려 본 결과가 `rne-review/예시_결과/`에 있습니다.

## 실제 제안서로

```
/rne-review-graph rne-review/proposals/창의-07_제안서.hwpx 창의-07
```

- `.hwpx` · `.docx` · `.md` · `.txt`는 스크립트가 바로 읽고, `.pdf`는 Claude가 읽어 옮겨 적습니다.
- 구버전 `.hwp`는 한글에서 PDF나 HWPX로 저장한 뒤 넣어 주세요.
- 과제 ID는 부서에서 쓰는 번호(창의-07, 물03 등)를 그대로 쓰면 됩니다.

중간에 끊겼다면: `/rne-review-graph 창의-07`
전체 현황: `python3 .claude/skills/rne-review-graph/scripts/card.py list`

## 결과물

`rne-review/cards/<과제ID>/`

| 파일 | 내용 |
|---|---|
| `feedback.md` | 학생 팀에게 보낼 피드백 (교사용 정보는 빠져 있음) |
| `card.json` | 모든 단계의 기록 — 분야, 노드별 판정, 협의회 권고, 관문 회차, 결재 이력, 로그 |
| `nodes/*.md` | 교과·운영·협의회의 전문 검토문 (교사용) |
| `proposal.md`, `source/` | 원문과 원본 파일 |

## 우리 부서에 맞게 고치기

| 바꾸고 싶은 것 | 고칠 파일 |
|---|---|
| 관문 기준 (공통 검토 카드, 등급 A·B·C) | `.claude/skills/rne-review-graph/references/review-card.md` |
| 분야 판별 규칙·안전 플래그 | `.claude/skills/rne-review-graph/references/routing.md` |
| 예산·일정·지도 기준 숫자 | `rne-review/context/운영기준.md` — 빈칸(개인 사용 기자재, 안전교육 절차 등)을 채우면 운영 노드가 그대로 씁니다 |
| 노드별 지시문·분량 | `.claude/agents/*.md` |
| 속도와 비용 | 에이전트의 `model:` 줄 (`inherit` → `sonnet`이면 빨라짐) |
| 흐름 자체 (노드 추가 등) | `graph.yaml`과 `scripts/card.py`의 `compute_next`를 함께 |

관문 기준은 2학기 파일럿 중인 공통 검토 카드로 바꿔 쓰도록 만들었습니다. 항목 ID(G1~)와 등급 표기만 유지하면 스크립트는 그대로 동작합니다.

## 알아 둘 점

- 노드 에이전트는 `permissionMode: acceptEdits`로 파일을 씁니다(편집할 때마다 묻지 않음). 쓰는 곳은 `rne-review/cards/<과제ID>/` 안으로 제한하도록 지시돼 있습니다. 매번 확인하고 싶으면 그 줄을 지우세요.
- 처음 실행할 때 `python3 … card.py` 실행 허락을 물으면 "항상 허용"을 고르면 편합니다.
- 제안서 한 건에 에이전트가 8~9번(재검토하면 더) 불립니다. 시험 환경에서는 노드 하나에 몇 분에서 수십 분이 걸렸습니다. 여러 건을 돌릴 때는 교과 노드의 `model`을 `sonnet`으로 바꿔 보세요.
- 오케스트레이터는 스스로 결재하지 않도록 되어 있습니다. 결재 질문에 답하지 않으면 그 자리에서 멈춥니다.
- 분야 판별 노드는 학생 이름과 학년만 카드로 옮기고 학번·연락처는 옮기지 않습니다.

## 파일 구성

```
rne-review-graph/
├── README.md
├── .claude/
│   ├── skills/rne-review-graph/
│   │   ├── SKILL.md              오케스트레이터 (/rne-review-graph)
│   │   ├── graph.yaml            그래프 지도 — 노드·간선·규칙
│   │   ├── references/
│   │   │   ├── node-output.md    노드 결과 형식 규약
│   │   │   ├── routing.md        분야 판별 규칙
│   │   │   ├── review-card.md    관문 기준 (공통 검토 카드)
│   │   │   └── fallback-rubric.md
│   │   └── scripts/card.py       과제 카드 도구 — 생성·추출·합치기·형식 검사·다음 단계·결재
│   └── agents/
│       ├── rne-router.md                분야 판별
│       ├── rne-review-{math,physics,chemistry,biology,earth,cs}.md
│       ├── rne-review-ops.md            운영
│       ├── rne-council.md               협의회
│       ├── rne-gate.md                  관문 (읽기 전용 독립 검수)
│       └── rne-feedback-writer.md       학생 피드백
└── rne-review/
    ├── proposals/예시_물03_제안서.md    시험용 가상 제안서
    ├── context/운영기준.md
    ├── 예시_결과/                       예시 제안서를 돌린 결과 일부
    └── cards/                           과제 카드가 쌓이는 곳
```

## 시험한 것

- `card.py`: 접수 → 분야 판별 → 동시 검토 → 협의회 → 관문 재검토 → 결재 재검토 요청 → 다시 결재 → 피드백 → 완료, 관문 3회 미통과 시 결재로 넘기기, 형식이 틀린 결과 거부, HWPX·DOCX 본문 추출을 자동 시험으로 확인했습니다.
- 노드 지시문을 그대로 준 에이전트로 예시 제안서를 처음부터 끝까지 돌렸고, 모든 노드 결과가 형식 검사를 통과했습니다(관문 등급 B로 통과, 조건부 승인, 학생 피드백 약 4,100자).
