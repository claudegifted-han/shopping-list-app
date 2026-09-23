# 노드 결과 규약

모든 노드는 이 규약대로 **자기 결과 파일만** 쓴다. `card.json`은 절대 고치지 않는다.
결과는 오케스트레이터가 `card.py merge`로 형식 검사를 한 뒤 과제 카드에 합친다.
형식이 틀리면 합쳐지지 않고, 오류 메시지와 함께 그 노드만 다시 불린다.

파일 위치: `rne-review/cards/<과제ID>/nodes/`

| 노드 | 쓰는 파일 |
|---|---|
| 분야 판별 | `router.json` |
| 교과 (math, physics, chemistry, biology, earth, cs) | `<교과>.md` + `<교과>.json` |
| 운영 | `ops.md` + `ops.json` |
| 협의회 | `council.md` + `council.json` |
| 관문 | (쓰지 않음) JSON을 답으로 돌려주면 오케스트레이터가 `gate.json`으로 저장 |
| 학생 피드백 | `../feedback.md` + `feedback.json` |

공통 규칙

- 파일은 UTF-8 JSON 한 덩어리. 코드 블록 울타리(```)나 설명 문장을 붙이지 않는다.
- 첫 키는 `"node"`이고 값은 노드 이름(파일 이름과 같음).
- 제안서에 없는 사실을 단정하지 않는다. 추정이면 문장에 "추정"을 쓴다.
- `evidence`는 제안서의 해당 문장 일부(40자 이내)나 절 제목을 그대로 옮긴다. 예: `"4.2 실험 방법 — 조건별 1회 측정"`
- 재검토일 때는 `revision_note`에 무엇을 고쳤는지 한두 문장으로 적는다.

## router.json

```json
{
  "node": "router",
  "subjects": ["physics", "cs"],
  "primary": "physics",
  "fusion": true,
  "flags": ["고위험장비", "생성AI활용"],
  "title": "제안서의 연구 주제 그대로",
  "team": ["학생 A", "학생 B"],
  "advisor": "지도교사 이름(있으면)",
  "reason": "왜 이 분야들인지 2~3문장. 근거가 된 제안서 표현을 포함."
}
```

- `subjects`: 1~3개, `math · physics · chemistry · biology · earth · cs` 중에서. 첫 값이 주 분야이고 `primary`와 같아야 한다.
- `flags`: 해당하는 것만 — `화학물질 · 생물시료 · 인간대상 · 동물 · 고위험장비 · 야외·야간활동 · 데이터라이선스 · 생성AI활용 · 고가장비구입`

## 교과 노드 `<교과>.json` (운영 노드도 같은 뼈대)

```json
{
  "node": "physics",
  "skill_used": "physics-rne-agent",
  "verdict": "보완 필요",
  "must_fix": [
    {"point": "무엇이 문제인가", "why": "왜 문제인가", "suggestion": "어떻게 고칠까", "evidence": "제안서 근거"}
  ],
  "should_fix": [
    {"point": "...", "suggestion": "..."}
  ],
  "strengths": ["잘한 점"],
  "questions": ["팀에게 물을 질문"],
  "safety_ethics": {"status": "조건부", "notes": "무엇을 확인·준비해야 하는가"},
  "keywords": ["선행 연구 검색어"],
  "summary": "2~3문장 요약",
  "revision_note": "재검토일 때만"
}
```

- `verdict`: `적합`(필수 수정 없음) · `보완 필요`(필수 수정 1개 이상, 주제는 유지 가능) · `부적합`(고교 R&E 규모에서 수행 불가하거나 안전·윤리상 진행 불가)
- `safety_ethics.status`: `문제없음` · `조건부` · `심의 필요`
- `skill_used`: 미리 불러온 스킬 이름. 스킬이 보이지 않아 대체 기준을 썼다면 `"fallback"`.
- `<교과>.md`: 그 교과 스킬의 "피드백 출력 형식" 그대로 쓴 전문 검토문.

## ops.json 추가 키

```json
{
  "node": "ops",
  "budget": {"status": "확인 필요", "requested": 2700000, "limit": 3000000, "notes": "..."},
  "schedule": {"status": "빠듯함", "notes": "..."},
  "advisor_load": {"status": "확인 필요", "notes": "지도교사 담당 팀 수를 알 수 없음"}
}
```

- `budget.status`: `적정` · `확인 필요` · `초과 우려`
- `schedule.status`: `가능` · `빠듯함` · `불가`

## council.json

```json
{
  "node": "council",
  "skill_used": "rne-council-simulator",
  "recommendation": "조건부 승인 권고",
  "agreements": ["노드들이 같은 의견인 점"],
  "disputes": [
    {"issue": "쟁점", "positions": {"cs": "...", "ops": "..."}, "suggested_resolution": "타협안"}
  ],
  "decisions_for_head": ["부장이 판단해야 할 것"],
  "priority_actions": [
    {"when": "즉시", "action": "..."},
    {"when": "1주 내", "action": "..."},
    {"when": "1개월 내", "action": "..."}
  ],
  "summary": "2~3문장 요약"
}
```

- `recommendation`: `승인 권고` · `조건부 승인 권고` · `보완 후 재심` · `반려 권고`
- `priority_actions[].when`: `즉시` · `1주 내` · `1개월 내`

## 관문 답 (오케스트레이터가 gate.json으로 저장)

```json
{
  "node": "gate",
  "round": 1,
  "result": "revise",
  "grade": "C",
  "checks": [
    {"id": "G1", "ok": true, "note": ""},
    {"id": "G2", "ok": false, "note": "cs의 필수 수정 2건에 근거가 없음"}
  ],
  "revise": [
    {"node": "cs", "instruction": "무엇이 빠졌고 무엇을 추가·수정하라는 구체적 지시"}
  ],
  "summary": "2~3문장"
}
```

- `result`: `pass` 또는 `revise`. `revise`면 `grade`는 `C`, `pass`면 `A` 또는 `B`.
- `revise[].node`: `math · physics · chemistry · biology · earth · cs · ops · council`

## feedback.json

```json
{"node": "feedback", "path": "feedback.md", "summary": "학생에게 보낸 피드백 한두 문장 요약"}
```
