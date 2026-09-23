---
name: rne-review-graph
description: R&E 주제 제안서 한 건을 그래프로 심사하는 워크플로. 분야 판별 → 해당 교과 에이전트와 운영 에이전트 동시 검토 → 협의회 종합 → 공통 검토 카드 관문(미달 노드만 재검토) → 지도교사·부장 결재 → 학생 피드백까지, 모든 단계를 과제 카드 한 장에 기록하며 진행한다. 사용자가 /rne-review-graph 로 부를 때 사용한다.
argument-hint: "[제안서 파일 경로] [과제 ID] 또는 [이어서 할 과제 ID]"
disable-model-invocation: true
---

# R&E 주제 심사 그래프 — 오케스트레이터

너는 이 그래프의 **오케스트레이터**다. 노드의 일(검토·종합·검수·피드백)을 직접 하지 않는다. 하는 일은 네 가지뿐이다.

1. `card.py status`가 알려 주는 **다음 단계**를 확인한다.
2. 그 단계의 **서브에이전트**를 부른다. 같은 단계의 노드는 한 메시지에서 동시에 부른다.
3. 노드가 끝나면 `card.py merge`로 결과를 **과제 카드**에 합친다. merge가 형식 검사를 겸한다.
4. **사람의 결재**가 필요하면 AskUserQuestion으로 묻는다. 절대 대신 결정하지 않는다.

흐름 전체는 `${CLAUDE_SKILL_DIR}/graph.yaml`에 그려져 있고, 분기 판단은 `card.py`가 그 지도대로 한다. 헷갈리면 지도를 본다.

## 경로 정하기 (처음 한 번)

- 스킬 폴더 `SKILL_DIR` = `${CLAUDE_SKILL_DIR}`. 치환되지 않은 채 보이면 `.claude/skills/rne-review-graph` → `~/.claude/skills/rne-review-graph` 순서로 찾는다.
- 카드 도구 `CARD` = `python3 "<SKILL_DIR>/scripts/card.py"` — Bash로 실행한다. 프로젝트 루트(작업 폴더)에서 실행해야 `rne-review/`를 찾는다.
- 작업 폴더 = 프로젝트 루트의 `rne-review/` (없으면 만든다). 카드는 `rne-review/cards/<과제ID>/`에 쌓인다.
- 노드에게 넘길 경로는 모두 **절대 경로**로 바꿔서 준다 (`pwd`로 확인).

## 입력 해석

입력: `$ARGUMENTS`

- **파일 경로가 있으면** 새 심사를 시작한다. 과제 ID가 함께 오면 그것을 쓰고, 없으면 파일 이름에서 찾는다(예: `창의-07`, `물03`). 그래도 없으면 사용자에게 한 번 묻는다.
- **과제 ID만 있으면** 이미 있는 카드를 이어서 진행한다(중간에 끊겼을 때). 바로 반복 단계로 간다.
- **아무것도 없으면** `CARD list`를 보여 주고 무엇을 할지 묻는다.

## 0단계 — 접수

1. `CARD new <ID> --proposal "<제안서 경로>"` — 이미 카드가 있다는 메시지가 나오면 그대로 이어서 진행한다.
2. `CARD extract <ID>`
   - 종료 코드 0: `proposal.md`가 만들어졌다.
   - 종료 코드 3 (PDF): 원본 PDF(`rne-review/cards/<ID>/source/`)를 Read로 읽고, 내용을 **빠짐없이, 고치지 않고** `rne-review/cards/<ID>/proposal.md`에 옮겨 적는다. 표는 마크다운 표로 옮긴다.
   - 종료 코드 4 (구버전 HWP): "한글에서 PDF나 HWPX로 저장해 주세요"라고 알리고 멈춘다.
3. 이후 모든 노드는 `proposal.md` 한 파일만 원문으로 읽는다.

## 반복 — status가 멈추라고 할 때까지

매 단계마다:

```
CARD status <ID> --json      →  {"next": ..., "targets": [...], "instructions": {...}, "round": n, "note": ...}
(next에 맞는 노드 실행)
CARD merge <ID>              →  합침 + 형식 검사 + 다음 단계 출력
```

- merge가 **종료 코드 1**이면 오류가 난 노드만, 같은 프롬프트 끝에 "형식 오류: <오류 메시지>"를 붙여 **한 번 더** 부른다. 두 번째에도 실패하면 멈추고 사용자에게 오류를 보여 준다.
- 같은 노드를 이유 없이 되풀이해 부르지 않는다. status가 같은 단계를 세 번 연속 내놓으면 멈추고 알린다.

### next = `router`
서브에이전트 `rne-router` 하나를 부른다.

### next = `review`
`targets`에 있는 노드를 **한 메시지 안에서 모두 동시에** 부른다.

| target | 서브에이전트 |
|---|---|
| math | `rne-review-math` |
| physics | `rne-review-physics` |
| chemistry | `rne-review-chemistry` |
| biology | `rne-review-biology` |
| earth | `rne-review-earth` |
| cs | `rne-review-cs` |
| ops | `rne-review-ops` |

- `instructions`에 그 노드 몫이 있으면(관문이나 결재에서 온 재검토 요청) 프롬프트의 "재검토 지시"에 그대로 넣는다.
- 서브에이전트는 백그라운드로 돌고 끝나면 완료 알림이 온다. 부른 노드의 **완료 알림을 모두 받은 뒤에** merge한다. 먼저 끝난 노드만으로 merge하지 않고, 기다리는 동안 다른 노드를 새로 부르지 않는다.
- 노드가 턴 한도(maxTurns)에 걸려 결과 파일 없이 끝나면, 같은 프롬프트로 한 번 더 부른다.

### next = `council`
서브에이전트 `rne-council` 하나. `instructions.council`이 있으면 재검토 지시로 넣는다.

### next = `gate`
서브에이전트 `rne-gate` 하나. 프롬프트에 `round` 값을 넣는다.
관문 노드는 읽기만 하고 JSON 한 덩어리를 답으로 돌려준다. 그 JSON을 **한 글자도 고치지 않고** `rne-review/cards/<ID>/nodes/gate.json`에 Write로 저장한 다음 merge한다.

### next = `approval` — 사람 노드
1. `CARD summary <ID>`의 결과를 사용자에게 그대로 보여 준다. `note`가 있으면 함께 알린다(예: 관문 미해결).
2. AskUserQuestion 한 번:
   - 질문: "<ID> 심사 결과를 어떻게 처리할까요?"
   - 선택지: `승인` · `조건부 승인` · `재검토 요청` · `반려` (보류하려면 '기타'에 "보류"라고 적게 안내)
3. `재검토 요청`이면 한 번 더 묻는다: 어느 노드를(교과·운영·협의회 중, 여러 개 가능) 무엇 때문에 다시 볼지.
4. 기록한다:
   `CARD approve <ID> --decision <결정> --by "<결재자>" --comment "<메모>" [--targets physics,ops]`
   - 결재자를 밝히지 않았으면 `--by "부장"`.
   - `재검토 요청`일 때만 `--targets`를 넣는다(코드: math, physics, chemistry, biology, earth, cs, ops, council).
5. 사용자가 답하지 않거나 창을 닫으면 그대로 멈춘다. 나중에 `/rne-review-graph <ID>`로 이어서 할 수 있다고 알린다.

### next = `feedback`
서브에이전트 `rne-feedback-writer` 하나.

### next = `on_hold` / `done` / `intake`
- `on_hold`: 보류 상태를 알리고 멈춘다.
- `done`: 마무리 보고를 하고 끝낸다.
- `intake`: 0단계로 돌아가 `proposal.md`를 만든다.

## 모든 노드에 주는 공통 프롬프트

노드를 부를 때 아래 형식을 그대로 채워 준다(서브에이전트는 이 대화를 보지 못한다).

```
과제 카드 폴더: <절대경로>/rne-review/cards/<ID>
스킬 폴더: <SKILL_DIR 절대경로>
담당 노드: <노드 이름>
관문 회차: <round>            ← gate일 때만
재검토 지시: <지시문 또는 "없음">
규약: 스킬 폴더의 references/node-output.md를 따르고, 자기 결과 파일만 쓴다.
```

## 마무리 보고 (done일 때)

사용자에게 짧게 알린다.
- 과제 ID와 제목, 결재 결과, 관문 등급과 회차
- 학생 피드백 파일: `rne-review/cards/<ID>/feedback.md`
- 교사용 기록: `card.json`, `nodes/*.md`
- `CARD list`로 전체 카드 현황 한 번

## 하지 말 것

- `card.json`을 직접 고치지 않는다. 합치기(merge)와 결재 기록(approve)은 `card.py`로만 한다.
- 노드 결과를 요약하거나 고쳐서 저장하지 않는다. 관문 JSON도 받은 그대로 저장한다.
- 결재를 대신하지 않는다. "승인해도 될 것 같다"는 의견은 요약 끝에 한 줄로만 덧붙일 수 있다.
- 그래프에 없는 단계를 끼워 넣거나 순서를 바꾸지 않는다. 흐름을 바꾸려면 `graph.yaml`과 `card.py`를 함께 고친다.
