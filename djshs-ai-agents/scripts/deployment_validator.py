#!/usr/bin/env python3
"""
DJSHS AI Agent System - 배포 검증 스크립트
배포 전 환경 설정 및 시스템 준비 상태를 검증합니다.

Usage:
    python deployment_validator.py --full        # 전체 검증
    python deployment_validator.py --env-only    # 환경변수만 검증
    python deployment_validator.py --files-only  # 파일 구조만 검증
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ValidationResult:
    """검증 결과"""
    category: str
    item: str
    passed: bool
    message: str
    severity: str  # "critical", "warning", "info"


class DeploymentValidator:
    """배포 검증 클래스"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results: List[ValidationResult] = []

    def add_result(
        self,
        category: str,
        item: str,
        passed: bool,
        message: str,
        severity: str = "warning"
    ):
        """검증 결과 추가"""
        self.results.append(ValidationResult(
            category=category,
            item=item,
            passed=passed,
            message=message,
            severity=severity
        ))

    # ==========================================
    # 환경 변수 검증
    # ==========================================

    def validate_environment(self) -> None:
        """환경 변수 검증"""
        print("\n🔍 환경 변수 검증 중...")

        required_vars = [
            ("NOTION_API_KEY", "critical", "Notion API 연동 필수"),
        ]

        optional_vars = [
            ("NOTION_DB_STUDENTS", "warning", "학생 명부 DB"),
            ("NOTION_DB_TEACHERS", "warning", "교직원 명부 DB"),
            ("NOTION_DB_RESEARCH", "warning", "자율연구 DB"),
            ("NOTION_DB_EVENTS", "warning", "학사일정 DB"),
            ("NOTION_DB_MEETINGS", "warning", "회의록 DB"),
            ("NOTION_DB_DOCUMENTS", "warning", "문서 DB"),
            ("NOTION_DB_CLUBS", "warning", "동아리 DB"),
            ("GITHUB_TOKEN", "info", "GitHub 연동 (선택)"),
        ]

        # 필수 환경 변수
        for var, severity, desc in required_vars:
            value = os.environ.get(var)
            if value:
                self.add_result("환경변수", var, True, f"✅ {desc} 설정됨", severity)
            else:
                self.add_result("환경변수", var, False, f"❌ {desc} 미설정", severity)

        # 선택 환경 변수
        for var, severity, desc in optional_vars:
            value = os.environ.get(var)
            if value:
                self.add_result("환경변수", var, True, f"✅ {desc} 설정됨", severity)
            else:
                self.add_result("환경변수", var, False, f"⚠️ {desc} 미설정", severity)

        # .env 파일 존재 여부
        env_file = self.project_root / ".env"
        if env_file.exists():
            self.add_result("환경변수", ".env 파일", True, "✅ .env 파일 존재", "info")
        else:
            self.add_result("환경변수", ".env 파일", False, "⚠️ .env 파일 없음", "warning")

    # ==========================================
    # 파일 구조 검증
    # ==========================================

    def validate_file_structure(self) -> None:
        """파일 구조 검증"""
        print("\n📁 파일 구조 검증 중...")

        required_dirs = [
            ("agents", "에이전트 정의"),
            ("prompts/system", "시스템 프롬프트"),
            ("config", "설정 파일"),
            ("templates", "템플릿"),
            ("tools", "도구"),
            ("data", "데이터"),
            ("docs", "문서"),
        ]

        required_files = [
            ("CLAUDE.md", "프로젝트 설명"),
            ("config/agents.yaml", "에이전트 설정"),
            ("config/workflows.yaml", "워크플로우 설정"),
            ("config/mcp.json", "MCP 설정"),
        ]

        # 디렉토리 검증
        for dir_path, desc in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists() and full_path.is_dir():
                self.add_result("파일구조", dir_path, True, f"✅ {desc} 디렉토리 존재", "critical")
            else:
                self.add_result("파일구조", dir_path, False, f"❌ {desc} 디렉토리 없음", "critical")

        # 필수 파일 검증
        for file_path, desc in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.add_result("파일구조", file_path, True, f"✅ {desc} 존재", "critical")
            else:
                self.add_result("파일구조", file_path, False, f"❌ {desc} 없음", "critical")

    # ==========================================
    # 에이전트 검증
    # ==========================================

    def validate_agents(self) -> None:
        """에이전트 파일 검증"""
        print("\n🤖 에이전트 검증 중...")

        required_agents = [
            "academic_affairs", "curriculum", "evaluation", "research", "edtech",
            "student_life", "afterschool", "career", "dormitory",
            "grade_1", "grade_2", "grade_3",
            "science_edu", "gifted_edu", "international", "admission",
            "ceo_strategy", "brainstorm"
        ]

        agents_dir = self.project_root / "agents"
        prompts_dir = self.project_root / "prompts" / "system"

        for agent in required_agents:
            # 에이전트 정의 파일
            agent_file = agents_dir / f"{agent}.md"
            if agent_file.exists():
                self.add_result("에이전트", f"{agent}.md", True, f"✅ {agent} 정의 존재", "critical")
            else:
                self.add_result("에이전트", f"{agent}.md", False, f"❌ {agent} 정의 없음", "critical")

            # 시스템 프롬프트 (일부 에이전트만)
            prompt_file = prompts_dir / f"{agent}.md"
            if prompt_file.exists():
                self.add_result("프롬프트", f"{agent}.md", True, f"✅ {agent} 프롬프트 존재", "warning")

    # ==========================================
    # 설정 파일 검증
    # ==========================================

    def validate_config(self) -> None:
        """설정 파일 검증"""
        print("\n⚙️ 설정 파일 검증 중...")

        # agents.yaml 검증
        agents_yaml = self.project_root / "config" / "agents.yaml"
        if agents_yaml.exists():
            try:
                import yaml
                with open(agents_yaml, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                if config and "agents" in config:
                    agent_count = len(config["agents"])
                    self.add_result("설정", "agents.yaml", True, f"✅ {agent_count}개 에이전트 정의됨", "critical")
                else:
                    self.add_result("설정", "agents.yaml", False, "❌ agents 섹션 없음", "critical")
            except ImportError:
                self.add_result("설정", "agents.yaml", True, "⚠️ YAML 파서 없음 (검증 생략)", "info")
            except Exception as e:
                self.add_result("설정", "agents.yaml", False, f"❌ 파싱 오류: {e}", "critical")

        # mcp.json 검증
        mcp_json = self.project_root / "config" / "mcp.json"
        if mcp_json.exists():
            try:
                with open(mcp_json, "r", encoding="utf-8") as f:
                    config = json.load(f)
                if "mcpServers" in config:
                    servers = list(config["mcpServers"].keys())
                    self.add_result("설정", "mcp.json", True, f"✅ MCP 서버: {', '.join(servers)}", "critical")
                else:
                    self.add_result("설정", "mcp.json", False, "❌ mcpServers 섹션 없음", "critical")
            except Exception as e:
                self.add_result("설정", "mcp.json", False, f"❌ 파싱 오류: {e}", "critical")

    # ==========================================
    # 도구 검증
    # ==========================================

    def validate_tools(self) -> None:
        """도구 파일 검증"""
        print("\n🔧 도구 검증 중...")

        required_tools = [
            ("notion_tools.py", "Notion 연동"),
            ("doc_generator.py", "문서 생성기"),
            ("schedule_tools.py", "일정 관리"),
            ("neis_helper.py", "NEIS 지원"),
            ("statistics_tools.py", "통계 분석"),
        ]

        tools_dir = self.project_root / "tools"

        for tool_file, desc in required_tools:
            full_path = tools_dir / tool_file
            if full_path.exists():
                # 기본 문법 검증
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    compile(content, tool_file, "exec")
                    self.add_result("도구", tool_file, True, f"✅ {desc} 정상", "warning")
                except SyntaxError as e:
                    self.add_result("도구", tool_file, False, f"❌ {desc} 문법 오류: {e}", "critical")
            else:
                self.add_result("도구", tool_file, False, f"⚠️ {desc} 파일 없음", "warning")

    # ==========================================
    # 보안 검증
    # ==========================================

    def validate_security(self) -> None:
        """보안 설정 검증"""
        print("\n🔒 보안 검증 중...")

        # .gitignore 확인
        gitignore = self.project_root / ".gitignore"
        sensitive_patterns = [".env", "*.key", "credentials", "secret"]

        if gitignore.exists():
            with open(gitignore, "r", encoding="utf-8") as f:
                content = f.read().lower()

            for pattern in sensitive_patterns:
                if pattern.lower() in content:
                    self.add_result("보안", f".gitignore ({pattern})", True, f"✅ {pattern} 제외됨", "critical")
                else:
                    self.add_result("보안", f".gitignore ({pattern})", False, f"⚠️ {pattern} 미제외", "warning")
        else:
            self.add_result("보안", ".gitignore", False, "❌ .gitignore 파일 없음", "critical")

        # 민감 파일 노출 확인
        sensitive_files = [".env", ".env.local", "credentials.json", "secrets.yaml"]
        for sensitive in sensitive_files:
            full_path = self.project_root / sensitive
            if full_path.exists():
                self.add_result("보안", sensitive, False, f"⚠️ {sensitive} 파일이 존재함 - 커밋 주의!", "warning")

    # ==========================================
    # 결과 리포트
    # ==========================================

    def run_all_validations(self) -> None:
        """전체 검증 실행"""
        self.validate_environment()
        self.validate_file_structure()
        self.validate_agents()
        self.validate_config()
        self.validate_tools()
        self.validate_security()

    def print_report(self) -> Tuple[int, int, int]:
        """검증 결과 리포트 출력"""
        print("\n" + "="*60)
        print("📊 배포 검증 결과 리포트")
        print(f"   검증 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        passed = 0
        failed = 0
        warnings = 0

        for category, items in categories.items():
            print(f"\n📌 {category}")
            print("-" * 40)
            for item in items:
                if item.passed:
                    passed += 1
                elif item.severity == "critical":
                    failed += 1
                else:
                    warnings += 1
                print(f"   {item.message}")

        print("\n" + "="*60)
        print("📈 요약")
        print("="*60)
        print(f"   ✅ 통과: {passed}")
        print(f"   ❌ 실패: {failed}")
        print(f"   ⚠️ 경고: {warnings}")
        print(f"   📊 총계: {len(self.results)}")

        if failed == 0:
            print("\n🎉 배포 준비 완료!")
            status = "READY"
        elif failed <= 3:
            print("\n⚠️ 일부 항목 수정 필요")
            status = "NEEDS_ATTENTION"
        else:
            print("\n❌ 배포 불가 - 문제 해결 필요")
            status = "NOT_READY"

        print(f"\n   배포 상태: {status}")
        print("="*60)

        return passed, failed, warnings

    def export_report(self, output_path: str = "deployment_report.json") -> None:
        """검증 결과 JSON 내보내기"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "results": [
                {
                    "category": r.category,
                    "item": r.item,
                    "passed": r.passed,
                    "message": r.message,
                    "severity": r.severity
                }
                for r in self.results
            ],
            "summary": {
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed and r.severity == "critical"),
                "warnings": sum(1 for r in self.results if not r.passed and r.severity != "critical"),
                "total": len(self.results)
            }
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📄 리포트 저장: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="DJSHS AI Agent System - 배포 검증"
    )
    parser.add_argument(
        "--project-root", "-r",
        help="프로젝트 루트 디렉토리",
        default="."
    )
    parser.add_argument(
        "--full", "-f",
        action="store_true",
        help="전체 검증"
    )
    parser.add_argument(
        "--env-only", "-e",
        action="store_true",
        help="환경변수만 검증"
    )
    parser.add_argument(
        "--files-only",
        action="store_true",
        help="파일 구조만 검증"
    )
    parser.add_argument(
        "--export", "-x",
        help="결과를 JSON으로 내보내기"
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🚀 DJSHS AI Agent System - 배포 검증 도구")
    print("="*60)

    validator = DeploymentValidator(args.project_root)

    if args.env_only:
        validator.validate_environment()
    elif args.files_only:
        validator.validate_file_structure()
    else:
        validator.run_all_validations()

    passed, failed, warnings = validator.print_report()

    if args.export:
        validator.export_report(args.export)

    # 종료 코드
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
