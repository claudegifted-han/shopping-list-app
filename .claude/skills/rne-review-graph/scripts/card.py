#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R&E 주제 심사 그래프 — 과제 카드 도구 (파이썬 표준 라이브러리만 사용)

과제 카드(card.json)는 그래프의 공유 기록이다.
  - 노드(서브에이전트)는 cards/<ID>/nodes/<노드>.json 에 자기 결과만 쓴다.
  - card.json 은 이 스크립트만 고친다 (merge, approve).
  - 다음에 어느 노드를 부를지는 status 가 그래프 규칙(graph.yaml)대로 알려 준다.

명령
  new <ID> --proposal <파일> [--title 제목]   카드 만들기
  extract <ID>                               제안서를 proposal.md 로 옮기기
  merge <ID>                                 nodes/*.json 을 형식 검사 후 카드에 합치기
  validate <ID> [--node 이름]                형식 검사만
  status <ID> [--json]                       다음 단계 알려 주기
  summary <ID>                               결재용 요약 (마크다운)
  approve <ID> --decision 결정 [...]         결재 기록
  list                                       전체 카드 현황

작업 폴더는 기본값이 ./rne-review 이고, 환경변수 RNE_REVIEW_ROOT 로 바꿀 수 있다.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(os.environ.get("RNE_REVIEW_ROOT", "rne-review"))

SUBJECTS = ["math", "physics", "chemistry", "biology", "earth", "cs"]
REVIEWERS = SUBJECTS + ["ops"]
LABEL = {
    "math": "수학", "physics": "물리", "chemistry": "화학", "biology": "생명과학",
    "earth": "지구과학", "cs": "정보·AI", "ops": "운영", "router": "분야 판별",
    "council": "협의회", "gate": "관문", "feedback": "학생 피드백", "approval": "결재",
    "intake": "접수",
}
FLAGS = ["화학물질", "생물시료", "인간대상", "동물", "고위험장비", "야외·야간활동",
         "데이터라이선스", "생성AI활용", "고가장비구입"]
VERDICTS = ["적합", "보완 필요", "부적합"]
SAFETY = ["문제없음", "조건부", "심의 필요"]
BUDGET = ["적정", "확인 필요", "초과 우려"]
SCHEDULE = ["가능", "빠듯함", "불가"]
RECS = ["승인 권고", "조건부 승인 권고", "보완 후 재심", "반려 권고"]
WHEN = ["즉시", "1주 내", "1개월 내"]
DECISIONS = ["승인", "조건부 승인", "재검토 요청", "반려", "보류"]
GRADES = ["A", "B", "C"]
MAX_GATE_ROUNDS = 3  # 첫 관문 + 재검토 2회. 넘으면 '미해결'로 결재에 넘긴다.
NODE_ORDER = ["router"] + REVIEWERS + ["council", "gate", "feedback"]


# ------------------------------------------------------------------ 기본 도구
def now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def safe_id(s):
    s = (s or "").strip()
    if not s or "/" in s or "\\" in s or s.startswith("."):
        die(f"과제 ID가 올바르지 않습니다: {s!r}", 2)
    return s


def cdir(cid):
    return ROOT / "cards" / safe_id(cid)


def load(cid):
    p = cdir(cid) / "card.json"
    if not p.exists():
        die(f"카드가 없습니다: {p}  (먼저 new 를 실행하세요)", 2)
    return json.loads(p.read_text(encoding="utf-8"))


def save(cid, card):
    card["updated_at"] = now()
    p = cdir(cid) / "card.json"
    tmp = p.with_name("card.json.tmp")
    tmp.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def read_json(path):
    """노드 결과 읽기. ```json 울타리가 있으면 벗겨 낸다."""
    path = Path(path)
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[A-Za-z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"{path.name}: JSON 형식 오류 — {e.msg} ({e.lineno}행 {e.colno}열)")
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: 최상위는 객체({{...}})여야 합니다")
    return data


def read_text_any(path):
    """UTF-8(BOM 포함)로 먼저 읽고, 안 되면 한글 윈도우 기본값(CP949)으로 읽는다.
    메모장·한글의 '유니코드' 저장(UTF-16, BOM 있음)도 읽는다."""
    raw = Path(path).read_bytes()
    encs = ["utf-8-sig", "cp949"]
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        encs.insert(0, "utf-16")
    for enc in encs:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")


def file_hash(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def seq(x):
    return (x or {}).get("_seq", 0)


def archive(card, key, old):
    if old:
        card["history"].append({"at": now(), "key": key, "data": old})


def _short(text, n):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


def latest_gate(card):
    rounds = [r for r in card["gate"]["rounds"] if r.get("cycle") == card["cycle"]]
    return (rounds[-1] if rounds else None), len(rounds)


# ---------------------------------------------------------------- 제안서 추출
def _local(tag):
    return tag.rsplit("}", 1)[-1]


def para_lines(root, p_tag="p", t_tag="t"):
    """HWPX(hp:p/hp:t)·DOCX(w:p/w:t) 공통: 문단마다 한 줄. 표 안 문단은 따로 한 줄."""
    lines = []

    def do_p(pel):
        buf, nested = [], []

        def walk(e):
            for ch in e:
                n = _local(ch.tag)
                if n == p_tag:
                    nested.append(ch)
                elif n == t_tag:
                    buf.append("".join(ch.itertext()))
                else:
                    walk(ch)

        walk(pel)
        line = "".join(buf).strip()
        if line:
            lines.append(line)
        for inner in nested:
            do_p(inner)

    def top(e):
        for ch in e:
            if _local(ch.tag) == p_tag:
                do_p(ch)
            else:
                top(ch)

    if _local(root.tag) == p_tag:
        do_p(root)
    else:
        top(root)
    return lines


# --------------------------------------------------------------- 노드 형식 검사
def _strs(x):
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def _items(items, key, need_evidence):
    errs = []
    if not isinstance(items, list):
        return [f"{key}는 배열이어야 합니다"]
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict):
            errs.append(f"{key}[{i}]는 객체여야 합니다")
            continue
        fields = ("point", "suggestion") + (("evidence",) if need_evidence else ())
        for f in fields:
            if not str(it.get(f, "")).strip():
                errs.append(f"{key}[{i}].{f}가 비어 있습니다")
    return errs


def check_node(name, x, d):
    e = []
    if x.get("node") != name:
        e.append(f'"node" 값이 "{name}"이어야 합니다 (지금: {x.get("node")!r})')
    if name == "router":
        subs = x.get("subjects")
        if not isinstance(subs, list) or not subs:
            e.append("subjects는 1개 이상인 배열이어야 합니다")
        else:
            bad = [s for s in subs if s not in SUBJECTS]
            if bad:
                e.append(f"subjects에 모르는 분야가 있습니다: {bad} (가능: {SUBJECTS})")
            if len(subs) > 3:
                e.append("subjects는 최대 3개입니다")
            if len(set(subs)) != len(subs):
                e.append("subjects에 같은 분야가 두 번 있습니다")
            if x.get("primary") != subs[0]:
                e.append("primary는 subjects의 첫 번째 값과 같아야 합니다")
        flags = x.get("flags", [])
        if not isinstance(flags, list) or [f for f in flags if f not in FLAGS]:
            e.append(f"flags는 다음 중에서만 고릅니다: {FLAGS}")
        if not str(x.get("reason", "")).strip():
            e.append("reason이 비어 있습니다")
        if x.get("team") is not None and not _strs(x["team"]):
            e.append('team은 문자열 배열이어야 합니다 (예: ["학생 A(2학년)", "학생 B(2학년)"])')
        for k in ("title", "advisor"):
            if x.get(k) is not None and not isinstance(x[k], str):
                e.append(f"{k}는 문자열이어야 합니다")
    elif name in REVIEWERS:
        verdict = x.get("verdict")
        if verdict not in VERDICTS:
            e.append(f"verdict는 {VERDICTS} 중 하나여야 합니다")
        e += _items(x.get("must_fix", []), "must_fix", True)
        e += _items(x.get("should_fix", []), "should_fix", False)
        if verdict == "적합" and x.get("must_fix"):
            e.append("verdict가 '적합'이면 must_fix가 비어 있어야 합니다")
        if verdict == "보완 필요" and not x.get("must_fix"):
            e.append("verdict가 '보완 필요'면 must_fix가 1개 이상이어야 합니다")
        se = x.get("safety_ethics")
        if not isinstance(se, dict) or se.get("status") not in SAFETY:
            e.append(f"safety_ethics.status는 {SAFETY} 중 하나여야 합니다")
        for k in ("strengths", "questions"):
            if not _strs(x.get(k, [])):
                e.append(f"{k}는 문자열 배열이어야 합니다")
        for k in ("summary", "skill_used"):
            if not str(x.get(k, "")).strip():
                e.append(f"{k}가 비어 있습니다")
        if name == "ops":
            if not isinstance(x.get("budget"), dict) or x["budget"].get("status") not in BUDGET:
                e.append(f"budget.status는 {BUDGET} 중 하나여야 합니다")
            if not isinstance(x.get("schedule"), dict) or x["schedule"].get("status") not in SCHEDULE:
                e.append(f"schedule.status는 {SCHEDULE} 중 하나여야 합니다")
        if not (d / "nodes" / f"{name}.md").exists():
            e.append(f"{name}.md(전문 검토문)가 없습니다")
    elif name == "council":
        if x.get("recommendation") not in RECS:
            e.append(f"recommendation은 {RECS} 중 하나여야 합니다")
        for k in ("agreements", "decisions_for_head"):
            if not _strs(x.get(k, [])):
                e.append(f"{k}는 문자열 배열이어야 합니다")
        disputes = x.get("disputes", [])
        if not isinstance(disputes, list) or any(
                not isinstance(i, dict) or not str(i.get("issue", "")).strip() for i in disputes):
            e.append("disputes는 issue가 있는 객체 배열이어야 합니다")
        acts = x.get("priority_actions", [])
        if not isinstance(acts, list) or any(
                not isinstance(i, dict) or i.get("when") not in WHEN or not str(i.get("action", "")).strip()
                for i in acts):
            e.append(f"priority_actions는 {{when: {'|'.join(WHEN)}, action}} 객체 배열이어야 합니다")
        if not str(x.get("summary", "")).strip():
            e.append("summary가 비어 있습니다")
        if not (d / "nodes" / "council.md").exists():
            e.append("council.md가 없습니다")
    elif name == "gate":
        result, grade = x.get("result"), x.get("grade")
        if result not in ("pass", "revise"):
            e.append('result는 "pass" 또는 "revise"여야 합니다')
        if grade not in GRADES:
            e.append(f"grade는 {GRADES} 중 하나여야 합니다")
        checks = x.get("checks")
        if not isinstance(checks, list) or not checks or any(
                not isinstance(c, dict) or not str(c.get("id", "")).strip() or not isinstance(c.get("ok"), bool)
                for c in checks):
            e.append("checks는 {id, ok(true/false), note} 객체 배열이어야 합니다")
        if result == "revise":
            rv = x.get("revise")
            if not isinstance(rv, list) or not rv:
                e.append("result가 revise면 revise 배열이 필요합니다")
            else:
                for i, it in enumerate(rv, 1):
                    if (not isinstance(it, dict) or it.get("node") not in REVIEWERS + ["council"]
                            or not str(it.get("instruction", "")).strip()):
                        e.append(f"revise[{i}]는 {{node: {REVIEWERS + ['council']} 중 하나, instruction}} 형식이어야 합니다")
            if grade != "C":
                e.append('result가 revise면 grade는 "C"여야 합니다')
        elif result == "pass" and grade == "C":
            e.append('result가 pass면 grade는 "A" 또는 "B"여야 합니다')
        if not str(x.get("summary", "")).strip():
            e.append("summary가 비어 있습니다")
    elif name == "feedback":
        if not (d / "feedback.md").exists():
            e.append("feedback.md(학생용 피드백)가 없습니다")
        if not str(x.get("summary", "")).strip():
            e.append("summary가 비어 있습니다")
    return e


# ----------------------------------------------------------- 그래프 규칙(간선)
def compute_next(card, d):
    """graph.yaml 의 간선을 코드로 옮긴 것. 무엇을 다음에 부를지 정한다."""

    def out(nxt, label, targets=None, note="", **kw):
        r = {"id": card["id"], "next": nxt, "label": label, "targets": targets or [], "note": note}
        r.update(kw)
        return r

    if not (Path(d) / "proposal.md").exists():
        return out("intake", "접수", note="proposal.md가 없습니다. extract를 실행하거나, PDF면 원문을 proposal.md로 옮겨 적으세요.")

    routing = card.get("routing")
    if not routing:
        return out("router", "분야 판별 대기", ["router"])

    pend = card.get("pending", {})
    needed = list(dict.fromkeys(list(routing.get("subjects", [])) + ["ops"]))
    have = set(card["reviews"]) | ({"ops"} if card.get("ops") else set())
    missing = [n for n in needed if n not in have]
    redo = [n for n in REVIEWERS if n in pend]
    targets = list(dict.fromkeys(missing + redo))
    if targets:
        instr = {n: pend[n]["instruction"] for n in targets if n in pend}
        return out("review", "검토 중", targets, instructions=instr,
                   note="대상 노드를 한 메시지에서 동시에 부르세요.")

    review_seq = max([seq(v) for v in card["reviews"].values()] + [seq(card.get("ops"))])
    council = card.get("council")
    if not council or seq(council) < review_seq or "council" in pend:
        instr = {"council": pend["council"]["instruction"]} if "council" in pend else {}
        return out("council", "협의회 대기", ["council"], instructions=instr)

    g, n_rounds = latest_gate(card)
    if not g or seq(g) < seq(council):
        return out("gate", "관문 대기", ["gate"], round=n_rounds + 1)

    appr = card.get("approval")
    if not appr or seq(appr) < seq(g) or (appr.get("decision") == "재검토 요청"):
        note = ""
        if card.get("gate_unresolved"):
            note = f"관문을 {n_rounds}번 거쳤지만 통과하지 못했습니다. 사람이 판단해 주세요."
        elif g.get("result") == "revise":
            note = "관문이 재검토를 요구했지만 대상이 없어 결재로 넘깁니다."
        return out("approval", "결재 대기", ["approval"], note=note,
                   gate_result=g.get("result"), grade=g.get("grade"), gate_rounds=n_rounds)

    dec = appr["decision"]
    if dec == "보류":
        return out("on_hold", "보류", note="결재가 보류되었습니다. 다시 결재하려면 approve 를 실행하세요.")
    fb = card.get("feedback")
    if not fb or seq(fb) < seq(appr):
        return out("feedback", "피드백 작성 대기", ["feedback"], decision=dec)
    return out("done", "완료(반려)" if dec == "반려" else "완료", decision=dec)


def place(card, name, data):
    if name == "router":
        archive(card, "routing", card.get("routing"))
        card["routing"] = data
        for k in ("title", "advisor"):
            if not card.get(k) and data.get(k):
                card[k] = data[k]
        if not card.get("team") and data.get("team"):
            card["team"] = data["team"]
    elif name in SUBJECTS:
        archive(card, name, card["reviews"].get(name))
        card["reviews"][name] = data
        card["pending"].pop(name, None)
    elif name in ("ops", "council", "feedback"):
        archive(card, name, card.get(name))
        card[name] = data
        card["pending"].pop(name, None)
    elif name == "gate":
        _, n = latest_gate(card)
        data["cycle"] = card["cycle"]
        data["round"] = n + 1
        card["gate"]["rounds"].append(data)
        if data["result"] == "revise":
            if n + 1 < MAX_GATE_ROUNDS and data.get("revise"):
                for it in data["revise"]:
                    card["pending"][it["node"]] = {"from": f"관문 {n + 1}회차", "instruction": it["instruction"]}
                card["gate_unresolved"] = False
            else:
                card["gate_unresolved"] = True
        else:
            card["gate_unresolved"] = False


# -------------------------------------------------------------------- 명령들
def cmd_new(a):
    cid = safe_id(a.id)
    d = cdir(cid)
    if (d / "card.json").exists():
        print(f"이미 있는 카드입니다: {d / 'card.json'} — 이어서 진행하세요 (status).")
        return
    src = Path(a.proposal).expanduser()
    if not src.exists():
        die(f"제안서 파일이 없습니다: {src}", 2)
    (d / "nodes").mkdir(parents=True, exist_ok=True)
    (d / "source").mkdir(exist_ok=True)
    dst = d / "source" / src.name
    shutil.copy2(src, dst)
    card = {
        "id": cid, "title": a.title or "", "team": [], "advisor": "",
        "proposal_source": str(dst), "proposal_text": "proposal.md",
        "created_at": now(), "updated_at": now(),
        "status": "접수", "cycle": 1, "seq": 0,
        "routing": None, "reviews": {}, "ops": None, "council": None,
        "gate": {"rounds": []}, "approval": None, "feedback": None,
        "pending": {}, "gate_unresolved": False,
        "history": [], "log": [], "_hashes": {},
    }
    card["log"].append({"at": now(), "node": "intake", "event": "카드 생성", "note": src.name})
    save(cid, card)
    print(f"카드 생성: {d / 'card.json'}")


def cmd_extract(a):
    cid = safe_id(a.id)
    card, d = load(cid), cdir(cid)
    src = Path(card["proposal_source"])
    out = d / "proposal.md"
    ext = src.suffix.lower()
    if ext in (".md", ".txt"):
        text = read_text_any(src)
    elif ext == ".hwpx":
        with zipfile.ZipFile(src) as z:
            secs = [n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)]
            secs.sort(key=lambda n: int(re.findall(r"\d+", n)[-1]))
            if not secs:
                die("HWPX 안에서 본문(Contents/section*.xml)을 찾지 못했습니다.", 5)
            lines = []
            for n in secs:
                lines += para_lines(ET.fromstring(z.read(n)))
        text = "\n\n".join(lines)
    elif ext == ".docx":
        with zipfile.ZipFile(src) as z:
            lines = para_lines(ET.fromstring(z.read("word/document.xml")))
        text = "\n\n".join(lines)
    elif ext == ".pdf":
        print(f"PDF입니다. 오케스트레이터가 원문을 Read로 읽어 {out} 에 빠짐없이 옮겨 적어 주세요.")
        sys.exit(3)
    elif ext == ".hwp":
        print("구버전 HWP는 바로 읽을 수 없습니다. 한글에서 PDF나 HWPX로 저장한 뒤 다시 실행해 주세요.")
        sys.exit(4)
    else:
        die(f"지원하지 않는 형식입니다: {ext} (md, txt, hwpx, docx, pdf 지원)", 2)
    body = text.strip()
    if len(body) < 50:
        die(f"추출된 글이 너무 짧습니다({len(body)}자). 파일 내용을 확인해 주세요.", 5)
    out.write_text(f"<!-- 원본: {src.name} · 추출: {now()} -->\n\n{body}\n", encoding="utf-8")
    card["log"].append({"at": now(), "node": "intake", "event": "제안서 추출", "note": f"{len(body)}자"})
    save(cid, card)
    print(f"제안서 추출: {out} ({len(body)}자)")


def cmd_merge(a):
    cid = safe_id(a.id)
    card, d = load(cid), cdir(cid)
    nd = d / "nodes"
    merged, errors = [], []
    for name in NODE_ORDER:
        p = nd / f"{name}.json"
        if not p.exists():
            continue
        h = file_hash(p)
        if card["_hashes"].get(name) == h:
            continue
        try:
            data = read_json(p)
        except ValueError as ex:
            errors.append(str(ex))
            continue
        errs = check_node(name, data, d)
        if errs:
            errors += [f"{name}.json: {m}" for m in errs]
            continue
        card["seq"] += 1
        data["_seq"] = card["seq"]
        data["_merged_at"] = now()
        place(card, name, data)
        card["_hashes"][name] = h
        merged.append(name)
        card["log"].append({"at": now(), "node": name, "event": "결과 합침",
                            "note": str(data.get("summary", ""))[:80]})
    extra = sorted(p.name for p in nd.glob("*.json") if p.stem not in NODE_ORDER)
    nxt = compute_next(card, d)
    card["status"] = nxt["label"]
    save(cid, card)
    if merged:
        print("합침: " + ", ".join(LABEL.get(m, m) for m in merged))
    else:
        print("새로 합친 결과가 없습니다.")
    if extra:
        print("무시한 파일(그래프에 없는 노드): " + ", ".join(extra))
    print(f"다음: {nxt['label']}" + (f" → {', '.join(LABEL.get(t, t) for t in nxt['targets'])}" if nxt["targets"] else ""))
    if errors:
        print("형식 오류가 있어 합치지 않은 결과가 있습니다:", file=sys.stderr)
        for m in errors:
            print("  - " + m, file=sys.stderr)
        sys.exit(1)


def cmd_validate(a):
    cid = safe_id(a.id)
    load(cid)
    d = cdir(cid)
    names = [a.node] if a.node else [n for n in NODE_ORDER if (d / "nodes" / f"{n}.json").exists()]
    bad = 0
    for name in names:
        p = d / "nodes" / f"{name}.json"
        if not p.exists():
            print(f"✗ {name}: 파일이 없습니다 ({p})")
            bad += 1
            continue
        try:
            errs = check_node(name, read_json(p), d)
        except ValueError as ex:
            errs = [str(ex)]
        if errs:
            bad += 1
            print(f"✗ {name}")
            for m in errs:
                print("   - " + m)
        else:
            print(f"✓ {name}")
    sys.exit(1 if bad else 0)


def cmd_status(a):
    cid = safe_id(a.id)
    card, d = load(cid), cdir(cid)
    nxt = compute_next(card, d)
    if a.json:
        print(json.dumps(nxt, ensure_ascii=False))
        return
    lines = [f"[{card['id']}] {card.get('title') or '(제목 미정)'}", f"현재: {nxt['label']}"]
    if nxt["targets"]:
        lines.append("다음 노드: " + ", ".join(LABEL.get(t, t) for t in nxt["targets"]))
    for k, v in (nxt.get("instructions") or {}).items():
        lines.append(f"  - {LABEL.get(k, k)} 재검토 지시: {v}")
    if nxt["note"]:
        lines.append("참고: " + nxt["note"])
    print("\n".join(lines))


def cmd_summary(a):
    cid = safe_id(a.id)
    card = load(cid)
    r = card.get("routing") or {}
    L = [f"## {card['id']} · {card.get('title') or '(제목 미정)'}"]
    team = ", ".join(card.get("team") or []) or "-"
    L.append(f"- 팀: {team} · 지도교사: {card.get('advisor') or '-'}")
    subs = r.get("subjects", [])
    if subs:
        s = ", ".join(LABEL[x] + ("(주)" if x == r.get("primary") else "") for x in subs)
        if r.get("flags"):
            s += " · 확인할 점: " + ", ".join(r["flags"])
        L.append("- 분야: " + s)
    rows = [(k, card["reviews"][k]) for k in SUBJECTS if k in card["reviews"]]
    if card.get("ops"):
        rows.append(("ops", card["ops"]))
    if rows:
        L += ["", "| 노드 | 판정 | 필수 수정 | 안전·윤리 |", "|---|---|---|---|"]
        for k, x in rows:
            L.append(f"| {LABEL[k]} | {x.get('verdict')} | {len(x.get('must_fix', []))}건 | "
                     f"{(x.get('safety_ethics') or {}).get('status', '-')} |")
        L.append("")
    ops = card.get("ops")
    if ops:
        L.append(f"- 운영: 예산 {ops['budget']['status']} · 일정 {ops['schedule']['status']}")
    c = card.get("council")
    if c:
        L.append(f"- 협의회 권고: {c['recommendation']}")
        for dsp in c.get("disputes", [])[:3]:
            L.append(f"  - 쟁점: {dsp['issue']}")
        for q in c.get("decisions_for_head", [])[:3]:
            L.append(f"  - 부장 판단 필요: {_short(q, 110)}")
    g, n = latest_gate(card)
    if g:
        if g["result"] == "pass":
            state = "통과"
        elif card.get("gate_unresolved"):
            state = "미통과 (재검토 한도 도달)"
        else:
            state = "재검토 필요"
        L.append(f"- 관문: {state} · 등급 {g.get('grade')} · {n}회차")
    fallback = [LABEL[k] for k, x in rows if x.get("skill_used") == "fallback"]
    if fallback:
        L.append(f"- 주의: {', '.join(fallback)} 노드는 교과 스킬을 찾지 못해 대체 기준으로 검토했습니다.")
    items = []
    for k, x in rows:
        for m in x.get("must_fix", []):
            items.append(f"[{LABEL[k]}] {_short(m['point'], 80)}")
    if items:
        L += ["", "필수 수정 (수정 방향은 nodes/<노드>.md 참고)"]
        L += [f"{i}. {t}" for i, t in enumerate(items, 1)]
    print("\n".join(L))


def cmd_approve(a):
    cid = safe_id(a.id)
    card, d = load(cid), cdir(cid)
    if a.decision not in DECISIONS:
        die(f"결정은 {DECISIONS} 중 하나여야 합니다.", 2)
    nxt = compute_next(card, d)
    if nxt["next"] not in ("approval", "on_hold", "feedback", "done"):
        die(f"아직 결재 단계가 아닙니다 (지금: {nxt['label']}).", 2)
    targets = [t.strip() for t in (a.targets or "").split(",") if t.strip()]
    if a.decision == "재검토 요청":
        bad = [t for t in targets if t not in REVIEWERS + ["council"]]
        if not targets or bad:
            die(f"재검토 요청에는 --targets 가 필요합니다 ({', '.join(REVIEWERS + ['council'])} 중).", 2)
    g, _ = latest_gate(card)
    card["seq"] += 1
    archive(card, "approval", card.get("approval"))
    card["approval"] = {
        "decision": a.decision, "by": a.by or "부장", "comment": a.comment or "",
        "targets": targets, "at": now(), "_seq": card["seq"],
        "gate_grade": (g or {}).get("grade"), "gate_unresolved": card.get("gate_unresolved", False),
    }
    if a.decision == "재검토 요청":
        card["cycle"] += 1
        card["gate_unresolved"] = False
        for t in targets:
            card["pending"][t] = {"from": "결재", "instruction": a.comment or "결재자가 재검토를 요청했습니다."}
    card["log"].append({"at": now(), "node": "approval", "event": f"결재: {a.decision}",
                        "note": (a.comment or "")[:80]})
    nxt = compute_next(card, d)
    card["status"] = nxt["label"]
    save(cid, card)
    print(f"결재 기록: {a.decision} ({card['approval']['by']}) → 다음: {nxt['label']}")


def cmd_list(a):
    base = ROOT / "cards"
    paths = sorted(base.glob("*/card.json")) if base.exists() else []
    if not paths:
        print("아직 카드가 없습니다.")
        return
    rows = [("과제 ID", "제목", "다음 단계", "갱신")]
    for p in paths:
        c = json.loads(p.read_text(encoding="utf-8"))
        nxt = compute_next(c, p.parent)
        rows.append((c["id"], (c.get("title") or "-")[:28], nxt["label"],
                     c.get("updated_at", "")[:16].replace("T", " ")))
    for r in rows:
        print(" | ".join(r))
    print(f"\n카드 {len(paths)}장")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="card.py", description="R&E 주제 심사 그래프 — 과제 카드 도구")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("new")
    p.add_argument("id")
    p.add_argument("--proposal", required=True)
    p.add_argument("--title")
    sp.add_parser("extract").add_argument("id")
    sp.add_parser("merge").add_argument("id")
    p = sp.add_parser("validate")
    p.add_argument("id")
    p.add_argument("--node", choices=NODE_ORDER)
    p = sp.add_parser("status")
    p.add_argument("id")
    p.add_argument("--json", action="store_true")
    sp.add_parser("summary").add_argument("id")
    p = sp.add_parser("approve")
    p.add_argument("id")
    p.add_argument("--decision", required=True)
    p.add_argument("--by")
    p.add_argument("--comment")
    p.add_argument("--targets", help="재검토 요청일 때: physics,ops 처럼 쉼표로")
    sp.add_parser("list")
    a = ap.parse_args(argv)
    {"new": cmd_new, "extract": cmd_extract, "merge": cmd_merge, "validate": cmd_validate,
     "status": cmd_status, "summary": cmd_summary, "approve": cmd_approve, "list": cmd_list}[a.cmd](a)


if __name__ == "__main__":
    main()
