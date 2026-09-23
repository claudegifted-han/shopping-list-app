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

- Claude Code (웹, WSL Ubuntu 포함), `python3` — 스크립트는 표준 라이브러리만 씁니다.
- 기존 스킬 8개. Claude Code에서 `/skills`로 확인하세요.
  - Claude Code 웹: claude.ai에 올려 둔 스킬이 세션에 자동으로 동기화됩니다. 목록에는 `anthropic-skills:physics-rne-agent`처럼 보이지만, 에이전트의 `skills:` 줄에 적힌 짧은 이름(`physics-rne-agent`)으로도 그대로 연결됩니다.
  - 로컬: `~/.claude/skills/`에 있어야 합니다.

| 노드 | 쓰는 스킬 |
|---|---|
| 수학 · 물리 · 화학 | `math-rne-agent` · `physics-rne-agent` · `chemistry-rne-agent` |
| 생명 · 지구 · 정보 | `biology-rne-agent` · `earth-science-rne-agent` · `cs-rne-agent` |
| 운영 · 협의회 | `rne-operations-agent` · `rne-council-simulator` |

스킬 이름이 다르면 `.claude/agents/rne-review-*.md`의 `skills:` 줄을 고치세요.
스킬이 없으면 에이전트는 대체 기준(`references/fallback-rubric.md`)으로 검토하고, 결재 요약에 그 사실이 표시됩니다.

## 설치

이 저장소에 이미 설치되어 있습니다. **저장소 루트가 곧 프로젝트**이고, 스킬과 에이전트가 루트의 `.claude/` 안에 들어 있어 따로 설치할 것이 없습니다.

| 어디서 | 어떻게 |
|---|---|
| Claude Code 웹 | 이 저장소로 새 세션을 열면 `/rne-review-graph`와 노드 에이전트 11개가 바로 잡힙니다 |
| 로컬 (WSL 등) | 저장소를 `git clone` 한 뒤 저장소 루트에서 `claude` |
| 다른 프로젝트 | `.claude/skills/rne-review-graph/`와 `.claude/agents/rne-*.md`를 `~/.claude/` 아래 같은 위치로 복사 |

세션 도중에 `.claude/`를 새로 받았다면 에이전트는 다음 세션부터 잡힙니다. 새 세션을 여세요.

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

- **Claude Code 웹**: 제안서 파일을 채팅에 첨부한 뒤 `/rne-review-graph <첨부한 파일> 창의-07`처럼 부르세요. 첨부 파일은 세션 안의 업로드 폴더에 들어가므로 저장소에 올릴 필요가 없습니다.
- **로컬**: `rne-review/proposals/`에 넣고 위 명령처럼 부르세요. 이 폴더의 실제 제안서는 git에 올라가지 않습니다(아래 "공개 저장소" 참고).
- `.hwpx` · `.docx` · `.md` · `.txt`는 스크립트가 바로 읽고, `.pdf`는 Claude가 읽어 옮겨 적습니다. `.txt`는 UTF-8, 한글 윈도우 기본(CP949), 유니코드(UTF-16) 저장 모두 읽습니다.
- 구버전 `.hwp`는 한글에서 PDF나 HWPX로 저장한 뒤 넣어 주세요.
- 과제 ID는 부서에서 쓰는 번호(창의-07, 물03 등)를 그대로 쓰면 됩니다. 첨부 파일 이름 앞에는 임의의 글자가 붙으므로 ID를 함께 적어 주는 편이 확실합니다.

중간에 끊겼다면: `/rne-review-graph 창의-07` (Claude Code 웹에서는 카드가 그 세션의 작업 공간에만 있으므로 같은 세션 안에서 이어 가세요)
전체 현황: `python3 .claude/skills/rne-review-graph/scripts/card.py list`

## 결과물

`rne-review/cards/<과제ID>/`

| 파일 | 내용 |
|---|---|
| `feedback.md` | 학생 팀에게 보낼 피드백 (교사용 정보는 빠져 있음) |
| `card.json` | 모든 단계의 기록 — 분야, 노드별 판정, 협의회 권고, 관문 회차, 결재 이력, 로그 |
| `nodes/*.md` | 교과·운영·협의회의 전문 검토문 (교사용) |
| `proposal.md`, `source/` | 원문과 원본 파일 |

과제 카드는 git에 올라가지 않습니다. Claude Code 웹 세션은 끝나면 작업 공간이 지워지므로, `feedback.md`와 필요한 검토문은 세션이 끝나기 전에 앱에서 열어 복사하거나 내려받아 두세요.

## 우리 부서에 맞게 고치기

| 바꾸고 싶은 것 | 고칠 파일 |
|---|---|
| 관문 기준 (공통 검토 카드, 등급 A·B·C) | `.claude/skills/rne-review-graph/references/review-card.md` |
| 분야 판별 규칙·안전 플래그 | `.claude/skills/rne-review-graph/references/routing.md` — 플래그를 새로 만들면 `scripts/card.py`의 `FLAGS`와 `references/node-output.md`의 flags 줄에도 넣으세요 (자동 시험이 어긋남을 알려 줍니다) |
| 예산·일정·지도 기준 숫자 | `rne-review/context/운영기준.md` — 빈칸(개인 사용 기자재, 안전교육 절차 등)을 채우면 운영 노드가 그대로 씁니다 |
| 노드별 지시문·분량 | `.claude/agents/*.md` |
| 속도와 비용 | 에이전트의 `model:` 줄 (`inherit` → `sonnet`이면 빨라짐) |
| 흐름 자체 (노드 추가 등) | `graph.yaml`과 `scripts/card.py`의 `compute_next`를 함께 |

관문 기준은 2학기 파일럿 중인 공통 검토 카드로 바꿔 쓰도록 만들었습니다. 항목 ID(G1~)와 등급 표기만 유지하면 스크립트는 그대로 동작합니다.

무엇을 고쳤든 고친 뒤에는 자동 시험을 한 번 돌려 보세요 (아래 "시험한 것").

## 알아 둘 점

- 노드 에이전트는 `permissionMode: acceptEdits`로 파일을 씁니다(편집할 때마다 묻지 않음). 쓰는 곳은 `rne-review/cards/<과제ID>/` 안으로 제한하도록 지시돼 있습니다. 매번 확인하고 싶으면 그 줄을 지우세요.
- 처음 실행할 때 `python3 … card.py` 실행 허락을 물으면 "항상 허용"을 고르면 편합니다.
- 제안서 한 건에 에이전트가 8~9번(재검토하면 더) 불립니다. 시험 환경에서는 노드 하나에 몇 분에서 수십 분이 걸렸습니다. 여러 건을 돌릴 때는 교과 노드의 `model`을 `sonnet`으로 바꿔 보세요.
- 오케스트레이터는 스스로 결재하지 않도록 되어 있습니다. 결재 질문에 답하지 않으면 그 자리에서 멈춥니다.
- 분야 판별 노드는 학생 이름과 학년만 카드로 옮기고 학번·연락처는 옮기지 않습니다.
- **공개 저장소**: 이 저장소는 누구나 볼 수 있습니다. 그래서 `rne-review/.gitignore`가 과제 카드(`cards/` 안)와 실제 제안서(`proposals/` 안, `예시_`로 시작하는 파일 제외)를 git에서 빼 둡니다. 카드를 기록으로 남기려면 먼저 저장소를 비공개로 바꾼 뒤 그 규칙을 지우세요.
- 이 저장소에서 다른 작업을 할 때 심사 노드가 끼어들지 않습니다. 노드 에이전트는 모두 "오케스트레이터가 부를 때만" 쓰도록 적혀 있고, `/rne-review-graph`는 사람만 부를 수 있습니다.

## 파일 구성

```
(저장소 루트)
├── .claude/
│   ├── skills/rne-review-graph/
│   │   ├── SKILL.md              오케스트레이터 (/rne-review-graph)
│   │   ├── graph.yaml            그래프 지도 — 노드·간선·규칙
│   │   ├── references/
│   │   │   ├── node-output.md    노드 결과 형식 규약
│   │   │   ├── routing.md        분야 판별 규칙
│   │   │   ├── review-card.md    관문 기준 (공통 검토 카드)
│   │   │   └── fallback-rubric.md
│   │   ├── scripts/card.py       과제 카드 도구 — 생성·추출·합치기·형식 검사·다음 단계·결재
│   │   └── tests/test_card.py    자동 시험 — 흐름·형식 검사·추출·배선
│   └── agents/
│       ├── rne-router.md                분야 판별
│       ├── rne-review-{math,physics,chemistry,biology,earth,cs}.md
│       ├── rne-review-ops.md            운영
│       ├── rne-council.md               협의회
│       ├── rne-gate.md                  관문 (읽기 전용 독립 검수)
│       └── rne-feedback-writer.md       학생 피드백
└── rne-review/
    ├── README.md                        이 문서
    ├── .gitignore                       실제 카드·제안서를 git에서 빼는 규칙
    ├── proposals/예시_물03_제안서.md    시험용 가상 제안서
    ├── context/운영기준.md
    ├── 예시_결과/                       예시 제안서를 돌린 결과 일부
    └── cards/                           과제 카드가 쌓이는 곳 (git에 올라가지 않음)
```

## 시험한 것

자동 시험은 저장소 루트에서 이렇게 돌립니다. 임시 폴더에서 돌아 실제 `rne-review/`는 건드리지 않고, 몇 초면 끝납니다.

```bash
python3 -m unittest discover -s .claude/skills/rne-review-graph/tests -v
```

- `card.py`: 접수 → 분야 판별 → 동시 검토 → 협의회 → 관문 재검토 → 결재 재검토 요청 → 다시 결재 → 피드백 → 완료, 관문 3회 미통과 시 결재로 넘기기, 협의회만 되돌리기, 보류·반려, 형식이 틀린 결과 거부, HWPX·DOCX·텍스트(인코딩별) 본문 추출.
- 배선: `graph.yaml`·`SKILL.md`·에이전트 파일·`routing.md`·`node-output.md`·`card.py`의 노드·스킬·플래그·결재 선택지·관문 횟수가 서로 맞는지. 한쪽만 고치면 이 시험이 실패합니다.
- 노드 지시문을 그대로 준 에이전트로 예시 제안서를 처음부터 끝까지 돌렸고, 모든 노드 결과가 형식 검사를 통과했습니다(관문 등급 B로 통과, 조건부 승인, 학생 피드백 약 4,100자).
