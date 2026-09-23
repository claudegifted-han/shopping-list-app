#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R&E 주제 심사 그래프 — 자동 시험 (파이썬 표준 라이브러리만 사용)

두 가지를 확인한다.
  1. card.py 가 graph.yaml 의 간선대로 다음 단계를 고르고, 형식이 틀린 결과를 거부하는가
  2. 그래프 지도(graph.yaml) · 오케스트레이터(SKILL.md) · 에이전트 파일 · 참조 문서 · card.py 가
     서로 맞물리는가 (한쪽만 고쳤을 때 바로 드러나도록)

실행 (프로젝트 루트에서)
  python3 -m unittest discover -s .claude/skills/rne-review-graph/tests -v

시험마다 임시 폴더를 RNE_REVIEW_ROOT 로 쓰므로 실제 rne-review/ 는 건드리지 않는다.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True

SKILL_DIR = Path(__file__).resolve().parents[1]
CARD = SKILL_DIR / "scripts" / "card.py"
AGENTS_DIR = SKILL_DIR.parents[1] / "agents"  # <프로젝트>/.claude/agents 또는 ~/.claude/agents

_spec = importlib.util.spec_from_file_location("card", CARD)
card = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(card)

PROPOSAL = """※ 시험용 가상 제안서

| 항목 | 내용 |
|---|---|
| 연구 주제 | 스마트폰 센서로 재는 감쇠 진자의 감쇠 계수 |

## 4.2 실험 방법

- 추 9종 각각에 대해 진폭 30°에서 놓아 2분 동안 기록한다(조건별 1회 측정).
"""


# --------------------------------------------------------------- 노드 결과 만들기
def router_out(subjects=("physics", "cs"), **kw):
    d = {"node": "router", "subjects": list(subjects), "primary": subjects[0],
         "fusion": len(subjects) > 1, "flags": ["고위험장비", "생성AI활용"],
         "title": "스마트폰 센서로 재는 감쇠 진자의 감쇠 계수",
         "team": ["학생 A(2학년)", "학생 B(2학년)"], "advisor": "지도교사 O",
         "reason": "역학 실험이 주 분야이고 머신러닝 평가가 결론을 좌우한다."}
    d.update(kw)
    return d


def review_out(name, verdict="보완 필요", note=None):
    must = [] if verdict == "적합" else [
        {"point": f"{name} 필수 수정", "why": "한 번만 재면 불확도를 알 수 없다",
         "suggestion": "조건마다 3회 이상 반복한다", "evidence": "4.2 실험 방법 — 조건별 1회 측정"}]
    d = {"node": name, "skill_used": f"{name}-rne-agent", "verdict": verdict, "must_fix": must,
         "should_fix": [{"point": "참고 문헌이 블로그뿐이다", "suggestion": "논문을 3편 찾는다"}],
         "strengths": ["질문이 구체적이다"], "questions": ["반복은 몇 번인가?"],
         "safety_ethics": {"status": "조건부", "notes": "레이저 등급 확인"},
         "keywords": ["damped pendulum"], "summary": f"{name} 검토 요약"}
    if name == "ops":
        d["budget"] = {"status": "확인 필요", "requested": 2700000, "limit": 3000000, "notes": "태블릿"}
        d["schedule"] = {"status": "빠듯함", "notes": "10월에 몰림"}
        d["advisor_load"] = {"status": "확인 필요", "notes": "담당 팀 수를 알 수 없음"}
    if note:
        d["revision_note"] = note
    return d


def council_out(note=None):
    d = {"node": "council", "skill_used": "rne-council-simulator",
         "recommendation": "조건부 승인 권고", "agreements": ["반복 측정이 필요하다"],
         "disputes": [{"issue": "측정 방식", "positions": {"physics": "떼자", "cs": "두자"},
                       "suggested_resolution": "예비 실험으로 정한다"}],
         "decisions_for_head": ["조건 이행 확인 방식"],
         "priority_actions": [{"when": "즉시", "action": "수정 제안서 제출"},
                              {"when": "1주 내", "action": "예비 실험"}],
         "summary": "조건부 승인을 권고한다."}
    if note:
        d["revision_note"] = note
    return d


def gate_out(result="pass", grade="B", revise=(), rnd=1):
    return {"node": "gate", "round": rnd, "result": result, "grade": grade,
            "checks": [{"id": f"G{i}", "ok": result == "pass" or i != 2, "note": ""} for i in range(1, 9)],
            "revise": [{"node": n, "instruction": f"{n}: 근거를 보강하라"} for n in revise],
            "summary": "관문 판정 요약"}


def hwpx(path, sections):
    ns = ('xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
          'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"')
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/hwp+zip")
        for i, body in sections.items():
            z.writestr(f"Contents/section{i}.xml",
                       f'<?xml version="1.0" encoding="UTF-8"?><hs:sec {ns}>{body}</hs:sec>')


def hp_p(text):
    return f"<hp:p><hp:run><hp:t>{text}</hp:t></hp:run></hp:p>"


def docx(path, body):
    ns = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml",
                   f'<?xml version="1.0" encoding="UTF-8"?><w:document {ns}><w:body>{body}</w:body></w:document>')


def w_p(*runs):
    return "<w:p>" + "".join(f'<w:r><w:t xml:space="preserve">{r}</w:t></w:r>' for r in runs) + "</w:p>"


def frontmatter(path):
    """에이전트·스킬 파일 머리말(--- ... ---)을 읽는다. 목록(- 값)은 리스트로."""
    m = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    if not m:
        raise AssertionError(f"{path.name}: 머리말(---)이 없습니다")
    fm, key = {}, None
    for line in m.group(1).splitlines():
        item = re.match(r"\s+-\s+(.+)", line)
        if item and key:
            fm[key].append(item.group(1).strip())
        elif ":" in line:
            key, val = (s.strip() for s in line.split(":", 1))
            fm[key] = val.strip('"') if val else []
    return fm


# ------------------------------------------------------------------- 시험 틀
class GraphCase(unittest.TestCase):
    CID = "시험-01"

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.root = self.base / "rne-review"
        self.env = dict(os.environ, RNE_REVIEW_ROOT=str(self.root), PYTHONIOENCODING="utf-8")

    def run_card(self, *args, code=0):
        r = subprocess.run([sys.executable, str(CARD), *map(str, args)], env=self.env, cwd=self.base,
                           capture_output=True, text=True, encoding="utf-8")
        if code is not None:
            self.assertEqual(r.returncode, code, f"card.py {' '.join(map(str, args))}\n"
                                                 f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        return r

    @property
    def cdir(self):
        return self.root / "cards" / self.CID

    def start(self, cid=None, text=PROPOSAL):
        cid = cid or self.CID
        src = self.base / f"{cid}_제안서.md"
        src.write_text(text, encoding="utf-8")
        self.run_card("new", cid, "--proposal", src)
        self.run_card("extract", cid)

    def put(self, name, data, md=True):
        nodes = self.cdir / "nodes"
        (nodes / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        if md and name in card.REVIEWERS + ["council"]:
            (nodes / f"{name}.md").write_text(f"# {name} 전문 검토문\n", encoding="utf-8")

    def put_feedback(self, summary="학생 피드백 요약"):
        (self.cdir / "feedback.md").write_text("# 주제 심사 결과\n", encoding="utf-8")
        self.put("feedback", {"node": "feedback", "path": "feedback.md", "summary": summary})

    def merge(self, code=0):
        return self.run_card("merge", self.CID, code=code)

    def next(self):
        return json.loads(self.run_card("status", self.CID, "--json").stdout)

    def load(self):
        return json.loads((self.cdir / "card.json").read_text(encoding="utf-8"))

    def to_gate(self, subjects=("physics", "cs")):
        """접수 → 분야 판별 → 동시 검토 → 협의회까지 진행해 관문 앞에 세운다."""
        self.start()
        self.put("router", router_out(subjects))
        self.merge()
        for n in list(subjects) + ["ops"]:
            self.put(n, review_out(n))
        self.merge()
        self.put("council", council_out())
        self.merge()
        self.assertEqual(self.next()["next"], "gate")

    def to_approval(self):
        self.to_gate()
        self.put("gate", gate_out())
        self.merge()
        self.assertEqual(self.next()["next"], "approval")


# ------------------------------------------------------------- 1. 흐름(간선)
class FlowTest(GraphCase):
    def test_full_cycle_with_gate_retry_and_approval_rereview(self):
        self.start()
        self.assertEqual(self.next()["next"], "router")
        self.put("router", router_out())
        self.merge()
        nxt = self.next()
        self.assertEqual((nxt["next"], nxt["targets"]), ("review", ["physics", "cs", "ops"]))

        for n in ("physics", "cs", "ops"):  # 동시 검토: 모두 도착한 뒤 한 번에 합친다
            self.put(n, review_out(n))
        self.assertIn("합침", self.merge().stdout)
        self.assertEqual(self.next()["next"], "council")

        self.put("council", council_out())
        self.merge()
        nxt = self.next()
        self.assertEqual((nxt["next"], nxt["round"]), ("gate", 1))

        # 관문 1회차: 정보 노드만 다시
        self.put("gate", gate_out("revise", "C", ["cs"], 1))
        self.merge()
        nxt = self.next()
        self.assertEqual((nxt["next"], nxt["targets"]), ("review", ["cs"]))
        self.assertEqual(nxt["instructions"], {"cs": "cs: 근거를 보강하라"})

        self.put("cs", review_out("cs", note="근거 보강"))
        self.merge()
        self.assertEqual(self.next()["next"], "council")  # 검토가 바뀌면 협의회가 다시 모은다
        self.put("council", council_out(note="cs 재검토 반영"))
        self.merge()
        nxt = self.next()
        self.assertEqual((nxt["next"], nxt["round"]), ("gate", 2))

        self.put("gate", gate_out("pass", "B", rnd=2))
        self.merge()
        nxt = self.next()
        self.assertEqual(nxt["next"], "approval")
        self.assertEqual((nxt["gate_result"], nxt["grade"], nxt["gate_rounds"]), ("pass", "B", 2))

        summary = self.run_card("summary", self.CID).stdout
        self.assertIn("팀: 학생 A(2학년), 학생 B(2학년)", summary)
        self.assertIn("관문: 통과 · 등급 B · 2회차", summary)
        self.assertIn("협의회 권고: 조건부 승인 권고", summary)
        self.assertIn("[물리] physics 필수 수정", summary)

        # 결재: 재검토 요청 → 새 주기, 사람이 지목한 노드만
        self.run_card("approve", self.CID, "--decision", "재검토 요청", "--by", "부장",
                      "--comment", "측정 방식을 다시 보라", "--targets", "physics")
        nxt = self.next()
        self.assertEqual((nxt["next"], nxt["targets"]), ("review", ["physics"]))
        self.assertEqual(nxt["instructions"], {"physics": "측정 방식을 다시 보라"})
        self.assertEqual(self.load()["cycle"], 2)

        self.put("physics", review_out("physics", note="측정 방식 재검토"))
        self.merge()
        self.put("council", council_out(note="물리 재검토 반영"))
        self.merge()
        nxt = self.next()
        self.assertEqual((nxt["next"], nxt["round"]), ("gate", 1))  # 관문 횟수를 새로 센다
        self.put("gate", gate_out("pass", "A", rnd=1))
        self.merge()
        self.assertEqual(self.next()["next"], "approval")

        self.run_card("approve", self.CID, "--decision", "조건부 승인", "--comment", "조건 6개")
        nxt = self.next()
        self.assertEqual((nxt["next"], nxt["decision"]), ("feedback", "조건부 승인"))

        self.put_feedback("조건부 승인 안내")
        self.merge()
        nxt = self.next()
        self.assertEqual((nxt["next"], nxt["label"]), ("done", "완료"))

        c = self.load()
        self.assertEqual(c["status"], "완료")
        self.assertEqual([(r["cycle"], r["round"]) for r in c["gate"]["rounds"]], [(1, 1), (1, 2), (2, 1)])
        self.assertEqual(c["approval"]["decision"], "조건부 승인")
        self.assertIn("approval", [h["key"] for h in c["history"]])  # 앞선 결재는 이력으로 남는다
        self.assertEqual(c["pending"], {})
        self.assertIn("완료", self.run_card("list").stdout)

    def test_gate_gives_up_after_three_rounds(self):
        self.to_gate()
        for rnd in (1, 2):
            self.put("gate", gate_out("revise", "C", ["ops"], rnd))
            self.merge()
            nxt = self.next()
            self.assertEqual((nxt["next"], nxt["targets"]), ("review", ["ops"]))
            self.put("ops", review_out("ops", note=f"관문 {rnd}회차 반영"))
            self.merge()
            self.put("council", council_out(note=f"관문 {rnd}회차 반영"))
            self.merge()
            self.assertEqual(self.next()["round"], rnd + 1)
        self.put("gate", gate_out("revise", "C", ["ops"], 3))
        self.merge()
        nxt = self.next()
        self.assertEqual(nxt["next"], "approval")  # 3회차도 미달이면 미해결로 결재에 올린다
        self.assertIn("3번", nxt["note"])
        self.assertTrue(self.load()["gate_unresolved"])
        self.assertIn("미통과 (재검토 한도 도달)", self.run_card("summary", self.CID).stdout)

    def test_gate_can_send_back_to_council_only(self):
        self.to_gate()
        self.put("gate", gate_out("revise", "C", ["council"]))
        self.merge()
        nxt = self.next()
        self.assertEqual((nxt["next"], nxt["instructions"]), ("council", {"council": "council: 근거를 보강하라"}))
        self.put("council", council_out(note="종합 수정"))
        self.merge()
        nxt = self.next()
        self.assertEqual((nxt["next"], nxt["round"]), ("gate", 2))

    def test_status_without_proposal_md_goes_back_to_intake(self):
        src = self.base / "제안서.md"
        src.write_text(PROPOSAL, encoding="utf-8")
        self.run_card("new", self.CID, "--proposal", src)
        self.assertEqual(self.next()["next"], "intake")


# ------------------------------------------------------------------- 2. 결재
class ApprovalTest(GraphCase):
    def test_cannot_approve_before_approval_step(self):
        self.start()
        r = self.run_card("approve", self.CID, "--decision", "승인", code=2)
        self.assertIn("아직 결재 단계가 아닙니다", r.stderr)

    def test_decision_and_targets_are_checked(self):
        self.to_approval()
        self.run_card("approve", self.CID, "--decision", "대충 승인", code=2)
        self.run_card("approve", self.CID, "--decision", "재검토 요청", code=2)
        self.run_card("approve", self.CID, "--decision", "재검토 요청", "--targets", "art", code=2)
        self.assertIsNone(self.load()["approval"])  # 거부된 결재는 기록되지 않는다
        self.assertEqual(self.next()["next"], "approval")

    def test_hold_then_approve(self):
        self.to_approval()
        self.run_card("approve", self.CID, "--decision", "보류")
        self.assertEqual(self.next()["next"], "on_hold")
        self.run_card("approve", self.CID, "--decision", "승인", "--by", "지도교사")
        nxt = self.next()
        self.assertEqual((nxt["next"], nxt["decision"]), ("feedback", "승인"))
        self.assertEqual(self.load()["approval"]["by"], "지도교사")

    def test_rejection_still_sends_feedback(self):
        self.to_approval()
        self.run_card("approve", self.CID, "--decision", "반려", "--comment", "안전 문제")
        self.assertEqual(self.next()["next"], "feedback")
        self.put_feedback("반려 안내")
        self.merge()
        nxt = self.next()
        self.assertEqual((nxt["next"], nxt["label"]), ("done", "완료(반려)"))


# ------------------------------------------------------------- 3. 형식 검사
class ValidationTest(GraphCase):
    def assert_rejected(self, name, data, message, md=True):
        self.put(name, data, md=md)
        r = self.merge(code=1)
        self.assertIn(message, r.stderr)

    def test_router_rules(self):
        self.start()
        cases = [
            (router_out(("art",)), "모르는 분야"),
            (router_out(("physics", "cs"), primary="cs"), "primary"),
            (router_out(("math", "physics", "chemistry", "cs")), "최대 3개"),
            (router_out(("physics", "physics")), "두 번"),
            (router_out(flags=["방사능"]), "flags"),
            (router_out(reason=""), "reason"),
            (router_out(team="학생 A, 학생 B"), "team"),
        ]
        for data, message in cases:
            with self.subTest(message=message):
                self.assert_rejected("router", data, message)
                self.assertEqual(self.next()["next"], "router")
        self.put("router", router_out(advisor=None))  # 지도교사를 모르면 비워 둘 수 있다
        self.merge()
        self.assertEqual(self.next()["next"], "review")

    def test_review_rules(self):
        self.start()
        self.put("router", router_out())
        self.merge()
        fit_with_fix = dict(review_out("physics"), verdict="적합")
        no_evidence = review_out("physics")
        no_evidence["must_fix"][0]["evidence"] = ""
        cases = [
            ("physics", dict(review_out("physics"), verdict="좋음"), "verdict"),
            ("physics", fit_with_fix, "must_fix가 비어 있어야"),
            ("physics", dict(review_out("physics"), must_fix=[]), "1개 이상"),
            ("physics", no_evidence, "evidence"),
            ("physics", dict(review_out("physics"), safety_ethics={"status": "모름"}), "safety_ethics"),
            ("physics", dict(review_out("physics"), summary=""), "summary"),
            ("physics", dict(review_out("physics"), node="phys"), '"node"'),
            ("ops", dict(review_out("ops"), budget=None), "budget.status"),
            ("ops", dict(review_out("ops"), schedule={"status": "몰라"}), "schedule.status"),
        ]
        for name, data, message in cases:
            with self.subTest(message=message):
                self.assert_rejected(name, data, message)
        self.assert_rejected("cs", review_out("cs"), "cs.md", md=False)  # 전문 검토문 없이 JSON만

    def test_valid_results_merge_even_if_another_node_fails(self):
        self.start()
        self.put("router", router_out())
        self.merge()
        self.put("physics", review_out("physics"))
        self.put("cs", dict(review_out("cs"), verdict="좋음"))
        self.put("ops", review_out("ops"))
        self.merge(code=1)
        self.assertEqual(set(self.load()["reviews"]), {"physics"})
        self.assertEqual(self.next()["targets"], ["cs"])  # 틀린 노드만 다시 부른다

    def test_code_fence_is_stripped_and_broken_json_rejected(self):
        self.start()
        p = self.cdir / "nodes" / "router.json"
        p.write_text("{ 깨진 JSON", encoding="utf-8")
        self.assertIn("JSON 형식 오류", self.merge(code=1).stderr)
        p.write_text("```json\n" + json.dumps(router_out(), ensure_ascii=False) + "\n```", encoding="utf-8")
        self.merge()
        self.assertEqual(self.next()["next"], "review")

    def test_gate_rules(self):
        self.to_gate()
        cases = [
            (gate_out("revise", "B", ["cs"]), 'grade는 "C"'),
            (gate_out("pass", "C"), '"A" 또는 "B"'),
            (gate_out("revise", "C", []), "revise 배열"),
            (gate_out("revise", "C", ["art"]), "revise[1]"),
            (dict(gate_out(), checks=[]), "checks"),
            (dict(gate_out(), result="maybe"), "result"),
        ]
        for data, message in cases:
            with self.subTest(message=message):
                self.assert_rejected("gate", data, message)
        self.assertEqual(self.next()["next"], "gate")

    def test_unknown_node_file_is_ignored(self):
        self.start()
        (self.cdir / "nodes" / "extra.json").write_text("{}", encoding="utf-8")
        self.assertIn("무시한 파일", self.merge().stdout)

    def test_validate_command(self):
        self.start()
        self.put("router", router_out(("art",)))
        self.assertIn("✗ router", self.run_card("validate", self.CID, code=1).stdout)
        self.put("router", router_out())
        self.assertIn("✓ router", self.run_card("validate", self.CID, "--node", "router").stdout)


# ------------------------------------------------------------ 4. 접수·추출
class IntakeTest(GraphCase):
    def test_bad_ids_are_refused(self):
        src = self.base / "p.md"
        src.write_text(PROPOSAL, encoding="utf-8")
        for bad in ("../밖", ".숨김", "a/b"):
            with self.subTest(bad=bad):
                self.run_card("new", bad, "--proposal", src, code=2)

    def test_new_twice_keeps_existing_card(self):
        self.start()
        r = self.run_card("new", self.CID, "--proposal", self.base / f"{self.CID}_제안서.md")
        self.assertIn("이미 있는 카드", r.stdout)

    def test_missing_proposal_file(self):
        self.run_card("new", self.CID, "--proposal", self.base / "없는파일.md", code=2)

    def test_pdf_old_hwp_and_unknown_formats(self):
        for ext, code in ((".pdf", 3), (".hwp", 4), (".xyz", 2)):
            with self.subTest(ext=ext):
                cid = "형식-" + ext[1:]
                src = self.base / f"제안서{ext}"
                src.write_bytes(b"%PDF-1.4 dummy")
                self.run_card("new", cid, "--proposal", src)
                self.run_card("extract", cid, code=code)

    def test_too_short_text_is_refused(self):
        src = self.base / "짧음.md"
        src.write_text("제목만", encoding="utf-8")
        self.run_card("new", self.CID, "--proposal", src)
        self.run_card("extract", self.CID, code=5)

    def test_text_in_utf8_bom_cp949_and_utf16(self):
        body = "연구 주제: 감쇠 진자의 감쇠 계수 측정. 조건마다 세 번 반복한다. " * 3
        for enc in ("utf-8-sig", "cp949", "utf-16"):
            with self.subTest(enc=enc):
                cid = f"인코딩-{enc}"
                src = self.base / f"{cid}.txt"
                src.write_bytes(body.encode(enc))
                self.run_card("new", cid, "--proposal", src)
                self.run_card("extract", cid)
                text = (self.root / "cards" / cid / "proposal.md").read_text(encoding="utf-8")
                self.assertIn("감쇠 진자", text)
                self.assertNotIn("﻿", text)
                self.assertNotIn("�", text)

    def test_hwpx_sections_in_number_order_with_table_cells(self):
        table = ("<hp:p><hp:run><hp:tbl><hp:tr>"
                 f"<hp:tc><hp:subList>{hp_p('재료비')}</hp:subList></hp:tc>"
                 f"<hp:tc><hp:subList>{hp_p('250,000')}</hp:subList></hp:tc>"
                 "</hp:tr></hp:tbl></hp:run></hp:p>")
        filler = hp_p("스마트폰 가속도 센서로 감쇠 진자의 감쇠 계수를 재고 머신러닝으로 추정한다.")
        src = self.base / "창의-07_제안서.hwpx"
        hwpx(src, {0: hp_p("첫째 절") + filler, 10: hp_p("셋째 절"), 2: hp_p("둘째 절") + table})
        self.run_card("new", self.CID, "--proposal", src)
        self.run_card("extract", self.CID)
        text = (self.cdir / "proposal.md").read_text(encoding="utf-8")
        pos = [text.index(s) for s in ("첫째 절", "둘째 절", "재료비", "250,000", "셋째 절")]
        self.assertEqual(pos, sorted(pos))  # section2 → section10 순서 (글자 순서가 아니라 번호 순서)

    def test_docx_runs_tables_and_no_deleted_text(self):
        body = (w_p("연구 주제: ", "감쇠 진자")
                + w_p("스마트폰 가속도 센서로 감쇠 계수를 재고 머신러닝 모델로 추정한다.")
                + "<w:p><w:r><w:delText>지운 글</w:delText></w:r></w:p>"
                + f"<w:tbl><w:tr><w:tc>{w_p('기자재')}</w:tc><w:tc>{w_p('1,800,000')}</w:tc></w:tr></w:tbl>")
        src = self.base / "제안서.docx"
        docx(src, body)
        self.run_card("new", self.CID, "--proposal", src)
        self.run_card("extract", self.CID)
        text = (self.cdir / "proposal.md").read_text(encoding="utf-8")
        self.assertIn("연구 주제: 감쇠 진자", text)
        self.assertIn("기자재", text)
        self.assertIn("1,800,000", text)
        self.assertNotIn("지운 글", text)


# ------------------------------------------------------ 5. 그래프 배선(맞물림)
class WiringTest(unittest.TestCase):
    """graph.yaml · SKILL.md · 에이전트 · 참조 문서 · card.py 가 서로 맞는지 본다."""

    @classmethod
    def setUpClass(cls):
        read = lambda p: (SKILL_DIR / p).read_text(encoding="utf-8")  # noqa: E731
        cls.graph, cls.skill = read("graph.yaml"), read("SKILL.md")
        cls.routing, cls.contract = read("references/routing.md"), read("references/node-output.md")
        cls.review_card = read("references/review-card.md")
        cls.members = {k: (a, s) for k, a, s in re.findall(
            r"^\s+(\w+):\s+\{agent: ([\w-]+),\s*skill: ([\w-]+)", cls.graph, re.M)}
        cls.solo = re.findall(r"^\s+agent: ([\w-]+)", cls.graph, re.M)

    def agent(self, name):
        path = AGENTS_DIR / f"{name}.md"
        if not AGENTS_DIR.is_dir():
            self.skipTest(f"에이전트 폴더가 없습니다: {AGENTS_DIR}")
        self.assertTrue(path.exists(), f"그래프가 부르는 에이전트 파일이 없습니다: {path}")
        return frontmatter(path)

    def test_review_members_match_card_py(self):
        self.assertEqual(list(self.members), card.REVIEWERS)
        self.assertEqual(self.solo, ["rne-router", "rne-council", "rne-gate", "rne-feedback-writer"])

    def test_each_agent_file_matches_graph(self):
        for key, (agent, skill) in self.members.items():
            with self.subTest(agent=agent):
                fm = self.agent(agent)
                self.assertEqual(fm["name"], agent)
                self.assertEqual(fm.get("skills"), [skill], "graph.yaml 의 skill 과 에이전트 skills: 가 다릅니다")
                self.assertIn("Write", fm["tools"])
        for agent in self.solo:
            with self.subTest(agent=agent):
                self.assertEqual(self.agent(agent)["name"], agent)
        self.assertEqual(self.agent("rne-council").get("skills"), ["rne-council-simulator"])

    def test_node_agents_are_only_called_by_the_orchestrator(self):
        # 이 저장소의 다른 작업 중에 Claude 가 심사 노드를 멋대로 부르지 않도록
        for agent in [a for a, _ in self.members.values()] + self.solo:
            with self.subTest(agent=agent):
                self.assertIn("오케스트레이터가 부를 때만", self.agent(agent)["description"])

    def test_gate_is_read_only(self):
        tools = self.agent("rne-gate")["tools"]
        self.assertNotIn("Write", tools)
        self.assertNotIn("Edit", tools)

    def test_no_orphan_agent_files(self):
        if not AGENTS_DIR.is_dir():
            self.skipTest(f"에이전트 폴더가 없습니다: {AGENTS_DIR}")
        wired = {a for a, _ in self.members.values()} | set(self.solo)
        self.assertEqual({p.stem for p in AGENTS_DIR.glob("rne-*.md")}, wired)

    def test_orchestrator_is_user_only_and_its_table_matches_graph(self):
        fm = frontmatter(SKILL_DIR / "SKILL.md")
        self.assertEqual(fm["name"], "rne-review-graph")
        self.assertEqual(fm["disable-model-invocation"], "true")
        rows = dict(re.findall(r"^\| (\w+) \| `(rne-[\w-]+)` \|", self.skill, re.M))
        self.assertEqual(rows, {k: a for k, (a, _) in self.members.items()})

    def test_routing_table_matches_graph(self):
        rows = {c: (a, s) for c, a, s in re.findall(
            r"^\| (\w+) \| [^|]+ \| (rne-[\w-]+) \| ([\w-]+) \|$", self.routing, re.M)}
        self.assertEqual(rows, {k: v for k, v in self.members.items() if k != "ops"})

    def test_flags_are_the_same_everywhere(self):
        table = self.routing.split("## 플래그", 1)[1]
        in_routing = [f for f in re.findall(r"^\| ([^|]+?) \| [^|]+ \|$", table, re.M) if f != "플래그"]
        self.assertEqual(in_routing, card.FLAGS, "routing.md 플래그 표와 card.py FLAGS 가 다릅니다")
        line = re.search(r"`flags`: 해당하는 것만 — `([^`]+)`", self.contract).group(1)
        self.assertEqual(line.split(" · "), card.FLAGS, "node-output.md 플래그 목록과 card.py FLAGS 가 다릅니다")

    def test_decisions_and_gate_limit_match(self):
        options = re.search(r"options: \[([^\]]+)\]", self.graph).group(1)
        self.assertEqual([o.strip() for o in options.split(",")], card.DECISIONS)
        for doc in (self.graph, self.review_card):
            self.assertEqual(int(re.search(r"최대 (\d+)번", doc).group(1)), card.MAX_GATE_ROUNDS)


if __name__ == "__main__":
    unittest.main()
