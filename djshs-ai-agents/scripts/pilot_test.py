#!/usr/bin/env python3
"""
DJSHS AI Agent System - 파일럿 테스트 도구
IT 담당자 및 부장교사 파일럿 테스트를 위한 시나리오 실행 도구

Usage:
    python pilot_test.py --quick     # 빠른 테스트 (5개 시나리오)
    python pilot_test.py --full      # 전체 테스트 (모든 시나리오)
    python pilot_test.py --agent academic_affairs  # 특정 에이전트 테스트
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class TestScenario:
    """테스트 시나리오"""
    id: str
    name: str
    agent: str
    description: str
    input_prompt: str
    expected_behavior: List[str]
    difficulty: str  # "easy", "medium", "hard"


# 파일럿 테스트 시나리오
PILOT_SCENARIOS = [
    # IT 담당자용 (시스템 검증)
    TestScenario(
        id="SYS-001",
        name="시스템 연결 테스트",
        agent="edtech",
        description="MCP 서버 연결 및 기본 응답 테스트",
        input_prompt="@교육정보부 현재 시스템 상태를 확인해줘",
        expected_behavior=[
            "에이전트가 정상 응답",
            "한국어로 응답",
            "5초 이내 응답"
        ],
        difficulty="easy"
    ),
    TestScenario(
        id="SYS-002",
        name="Notion 연동 테스트",
        agent="academic_affairs",
        description="Notion 데이터베이스 조회 기능 테스트",
        input_prompt="@교무운영부 이번 달 학사일정 조회해줘",
        expected_behavior=[
            "학사일정 데이터 조회",
            "날짜 형식 정상",
            "한국어 응답"
        ],
        difficulty="medium"
    ),
    TestScenario(
        id="SYS-003",
        name="다중 에이전트 테스트",
        agent="brainstorm",
        description="브레인스토밍 에이전트 다부서 협의 테스트",
        input_prompt="@브레인스토밍 신학년 준비 관련 부서별 의견 수렴해줘",
        expected_behavior=[
            "여러 부서 의견 수렴",
            "구조화된 응답",
            "실행 가능한 제안"
        ],
        difficulty="hard"
    ),

    # 부장교사용 (기능 검증)
    TestScenario(
        id="FUNC-001",
        name="공문 작성 테스트",
        agent="academic_affairs",
        description="공문 초안 작성 기능 테스트",
        input_prompt="@교무운영부 교내 연수 안내 공문 작성해줘. 일시: 2월 15일, 장소: 시청각실",
        expected_behavior=[
            "공문 형식 준수",
            "필요 정보 포함",
            "수정 가능한 초안 제공"
        ],
        difficulty="easy"
    ),
    TestScenario(
        id="FUNC-002",
        name="회의록 정리 테스트",
        agent="academic_affairs",
        description="회의록 정리 기능 테스트",
        input_prompt="@교무운영부 다음 내용으로 회의록 정리해줘: 참석자-김교사, 이교사, 안건-신학년 준비, 결정사항-3월 1일까지 교육과정 확정",
        expected_behavior=[
            "회의록 템플릿 적용",
            "항목별 정리",
            "후속조치 명시"
        ],
        difficulty="easy"
    ),
    TestScenario(
        id="FUNC-003",
        name="자율연구 현황 조회",
        agent="gifted_edu",
        description="자율연구 프로젝트 현황 조회 테스트",
        input_prompt="@영재교육부 현재 진행 중인 2학년 심화연구 현황 정리해줘",
        expected_behavior=[
            "연구 목록 제공",
            "상태별 분류",
            "지도교사 정보 포함"
        ],
        difficulty="medium"
    ),
    TestScenario(
        id="FUNC-004",
        name="일정 관리 테스트",
        agent="curriculum",
        description="학사일정 관리 기능 테스트",
        input_prompt="@교육과정부 2월 중 예정된 시험 및 행사 일정 정리해줘",
        expected_behavior=[
            "날짜순 정렬",
            "일정 유형 분류",
            "담당부서 명시"
        ],
        difficulty="easy"
    ),
    TestScenario(
        id="FUNC-005",
        name="성적 분석 테스트",
        agent="evaluation",
        description="성적 분석 기능 테스트 (가상 데이터)",
        input_prompt="@교육평가부 지난 학기 수학 과목 성적 분포 분석 방법 설명해줘",
        expected_behavior=[
            "분석 방법론 제시",
            "통계 지표 설명",
            "시각화 제안"
        ],
        difficulty="medium"
    ),

    # 고급 시나리오
    TestScenario(
        id="ADV-001",
        name="CEO 모드 전략 기획",
        agent="ceo_strategy",
        description="전략기획실 종합 기획 테스트",
        input_prompt="@전략기획실 신학년 학교교육계획 주요 항목 초안 제안해줘",
        expected_behavior=[
            "종합적 관점 제시",
            "부서별 역할 분배",
            "실행 일정 제안"
        ],
        difficulty="hard"
    ),
    TestScenario(
        id="ADV-002",
        name="NEIS 기재 지원",
        agent="evaluation",
        description="NEIS 기재 요령 안내 테스트",
        input_prompt="@교육평가부 세부능력 및 특기사항 기재 시 주의사항 안내해줘",
        expected_behavior=[
            "교육부 기재요령 준수",
            "구체적 예시 제공",
            "금지 표현 안내"
        ],
        difficulty="medium"
    ),
]


class PilotTester:
    """파일럿 테스트 실행기"""

    def __init__(self, output_dir: str = None):
        self.scenarios = PILOT_SCENARIOS
        self.results: List[Dict[str, Any]] = []
        self.output_dir = Path(output_dir) if output_dir else Path("pilot_results")
        self.output_dir.mkdir(exist_ok=True)

    def get_scenarios_by_agent(self, agent: str) -> List[TestScenario]:
        """특정 에이전트 시나리오 필터링"""
        return [s for s in self.scenarios if s.agent == agent]

    def get_scenarios_by_difficulty(self, difficulty: str) -> List[TestScenario]:
        """난이도별 시나리오 필터링"""
        return [s for s in self.scenarios if s.difficulty == difficulty]

    def print_scenario(self, scenario: TestScenario) -> None:
        """시나리오 출력"""
        print(f"\n{'='*60}")
        print(f"📋 테스트 ID: {scenario.id}")
        print(f"   이름: {scenario.name}")
        print(f"   에이전트: {scenario.agent}")
        print(f"   난이도: {scenario.difficulty}")
        print(f"{'='*60}")
        print(f"\n📝 설명:\n   {scenario.description}")
        print(f"\n💬 입력 프롬프트:")
        print(f"   {scenario.input_prompt}")
        print(f"\n✅ 예상 동작:")
        for behavior in scenario.expected_behavior:
            print(f"   - {behavior}")

    def run_interactive_test(self, scenario: TestScenario) -> Dict[str, Any]:
        """대화형 테스트 실행"""
        self.print_scenario(scenario)

        print(f"\n{'─'*60}")
        print("⏳ 위 프롬프트를 Claude Code에 입력하고 결과를 확인하세요.")
        print("─"*60)

        # 결과 입력 받기
        print("\n🔍 테스트 결과를 입력하세요:")

        results = {}
        for i, behavior in enumerate(scenario.expected_behavior, 1):
            while True:
                response = input(f"   {i}. {behavior} [P/F/S]: ").strip().upper()
                if response in ["P", "F", "S"]:
                    results[behavior] = {
                        "P": "PASS",
                        "F": "FAIL",
                        "S": "SKIP"
                    }[response]
                    break
                print("      P(Pass), F(Fail), S(Skip) 중 하나를 입력하세요.")

        # 추가 메모
        notes = input("\n   📝 추가 메모 (없으면 Enter): ").strip()

        # 결과 저장
        test_result = {
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "agent": scenario.agent,
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "overall_pass": all(r == "PASS" for r in results.values()),
            "notes": notes
        }

        self.results.append(test_result)
        return test_result

    def run_quick_test(self) -> None:
        """빠른 테스트 (5개 시나리오)"""
        quick_scenarios = [
            s for s in self.scenarios
            if s.id in ["SYS-001", "FUNC-001", "FUNC-002", "FUNC-004", "FUNC-003"]
        ]

        print("\n" + "="*60)
        print("🚀 DJSHS AI Agent System - 빠른 파일럿 테스트")
        print(f"   시나리오 수: {len(quick_scenarios)}개")
        print("="*60)

        for scenario in quick_scenarios:
            self.run_interactive_test(scenario)

        self.print_summary()
        self.save_results()

    def run_full_test(self) -> None:
        """전체 테스트"""
        print("\n" + "="*60)
        print("🚀 DJSHS AI Agent System - 전체 파일럿 테스트")
        print(f"   시나리오 수: {len(self.scenarios)}개")
        print("="*60)

        for scenario in self.scenarios:
            self.run_interactive_test(scenario)

            cont = input("\n계속하시겠습니까? [Y/n]: ").strip().lower()
            if cont == "n":
                break

        self.print_summary()
        self.save_results()

    def run_agent_test(self, agent: str) -> None:
        """특정 에이전트 테스트"""
        agent_scenarios = self.get_scenarios_by_agent(agent)

        if not agent_scenarios:
            print(f"❌ '{agent}' 에이전트에 대한 시나리오가 없습니다.")
            return

        print("\n" + "="*60)
        print(f"🚀 DJSHS AI Agent System - {agent} 에이전트 테스트")
        print(f"   시나리오 수: {len(agent_scenarios)}개")
        print("="*60)

        for scenario in agent_scenarios:
            self.run_interactive_test(scenario)

        self.print_summary()
        self.save_results()

    def print_summary(self) -> None:
        """테스트 결과 요약"""
        if not self.results:
            print("\n⚠️ 실행된 테스트가 없습니다.")
            return

        passed = sum(1 for r in self.results if r["overall_pass"])
        failed = sum(1 for r in self.results if not r["overall_pass"])

        print("\n" + "="*60)
        print("📊 테스트 결과 요약")
        print("="*60)
        print(f"   ✅ 통과: {passed}")
        print(f"   ❌ 실패: {failed}")
        print(f"   📊 통과율: {passed / len(self.results) * 100:.1f}%")

        if failed > 0:
            print("\n❌ 실패한 테스트:")
            for r in self.results:
                if not r["overall_pass"]:
                    print(f"   - {r['scenario_id']}: {r['scenario_name']}")

    def save_results(self) -> str:
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"pilot_test_{timestamp}.json"

        report = {
            "test_date": datetime.now().isoformat(),
            "total_scenarios": len(self.results),
            "passed": sum(1 for r in self.results if r["overall_pass"]),
            "failed": sum(1 for r in self.results if not r["overall_pass"]),
            "results": self.results
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n💾 결과 저장: {output_file}")
        return str(output_file)

    def print_all_scenarios(self) -> None:
        """모든 시나리오 목록 출력"""
        print("\n" + "="*60)
        print("📋 파일럿 테스트 시나리오 목록")
        print("="*60)

        current_prefix = ""
        for scenario in self.scenarios:
            prefix = scenario.id.split("-")[0]
            if prefix != current_prefix:
                current_prefix = prefix
                category = {
                    "SYS": "🔧 시스템 테스트",
                    "FUNC": "⚙️ 기능 테스트",
                    "ADV": "🎯 고급 테스트"
                }.get(prefix, prefix)
                print(f"\n{category}")
                print("-"*40)

            diff_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}[scenario.difficulty]
            print(f"  {scenario.id} | {diff_emoji} | {scenario.name}")
            print(f"          └─ 에이전트: {scenario.agent}")


def main():
    parser = argparse.ArgumentParser(
        description="DJSHS AI Agent System - 파일럿 테스트"
    )
    parser.add_argument("--quick", "-q", action="store_true", help="빠른 테스트 (5개)")
    parser.add_argument("--full", "-f", action="store_true", help="전체 테스트")
    parser.add_argument("--agent", "-a", help="특정 에이전트 테스트")
    parser.add_argument("--list", "-l", action="store_true", help="시나리오 목록 출력")
    parser.add_argument("--output", "-o", help="결과 저장 디렉토리")

    args = parser.parse_args()

    tester = PilotTester(args.output)

    if args.list:
        tester.print_all_scenarios()
    elif args.quick:
        tester.run_quick_test()
    elif args.full:
        tester.run_full_test()
    elif args.agent:
        tester.run_agent_test(args.agent)
    else:
        # 기본: 시나리오 목록 출력
        tester.print_all_scenarios()
        print("\n💡 테스트 실행: python pilot_test.py --quick 또는 --full")


if __name__ == "__main__":
    main()
