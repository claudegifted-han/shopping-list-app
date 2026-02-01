#!/usr/bin/env python3
"""
DSHS AI Agent System - 사용 통계 리포트 생성기
일별/주별/월별 사용 현황 리포트를 생성합니다.

Usage:
    python generate_report.py --daily           # 일일 리포트
    python generate_report.py --weekly          # 주간 리포트
    python generate_report.py --monthly         # 월간 리포트
    python generate_report.py --format html     # HTML 형식 출력
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

# 상위 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

try:
    from monitoring import AgentMonitor, get_monitor
except ImportError:
    print("⚠️ monitoring 모듈을 찾을 수 없습니다.")
    print("   tools/monitoring.py 파일이 존재하는지 확인하세요.")
    sys.exit(1)


class ReportGenerator:
    """리포트 생성기"""

    AGENT_NAMES_KO = {
        "academic_affairs": "교무운영부",
        "curriculum": "교육과정부",
        "evaluation": "교육평가부",
        "research": "교육연구부",
        "edtech": "교육정보부",
        "student_life": "학생생활안전부",
        "afterschool": "방과후인성부",
        "career": "진로진학부",
        "dormitory": "사감부",
        "grade_1": "1학년부",
        "grade_2": "2학년부",
        "grade_3": "3학년부",
        "science_edu": "과학교육부",
        "gifted_edu": "영재교육부",
        "international": "국제교류부",
        "admission": "입학지원부",
        "ceo_strategy": "전략기획실",
        "brainstorm": "브레인스토밍"
    }

    def __init__(self, monitor: AgentMonitor = None):
        self.monitor = monitor or get_monitor()

    def _get_agent_name_ko(self, agent_id: str) -> str:
        """에이전트 한글명 반환"""
        return self.AGENT_NAMES_KO.get(agent_id, agent_id)

    def generate_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """일일 리포트 생성"""
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")

        report = {
            "type": "daily",
            "date": date_str,
            "generated_at": datetime.now().isoformat(),
            "summary": {},
            "agent_breakdown": {},
            "task_breakdown": {},
            "hourly_distribution": {},
            "errors": []
        }

        # 에이전트 통계
        agent_stats = self.monitor.get_agent_stats(days=1)
        total_calls = sum(s["total_calls"] for s in agent_stats.values())
        total_success = sum(s["success_calls"] for s in agent_stats.values())
        total_tokens = sum(s["total_tokens"] for s in agent_stats.values())

        report["summary"] = {
            "total_calls": total_calls,
            "success_calls": total_success,
            "success_rate": round(total_success / total_calls * 100, 1) if total_calls > 0 else 0,
            "total_tokens": total_tokens,
            "active_agents": len(agent_stats)
        }

        report["agent_breakdown"] = {
            self._get_agent_name_ko(k): v for k, v in agent_stats.items()
        }

        report["task_breakdown"] = self.monitor.get_task_type_stats(days=1)
        report["errors"] = self.monitor.get_error_summary(days=1)

        return report

    def generate_weekly_report(self, end_date: datetime = None) -> Dict[str, Any]:
        """주간 리포트 생성"""
        if end_date is None:
            end_date = datetime.now()

        start_date = end_date - timedelta(days=7)

        report = {
            "type": "weekly",
            "period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            },
            "generated_at": datetime.now().isoformat(),
            "summary": {},
            "daily_trend": [],
            "top_agents": [],
            "top_tasks": [],
            "efficiency_metrics": {},
            "recommendations": []
        }

        # 일별 추이
        daily_trend = self.monitor.get_daily_trend(7)
        report["daily_trend"] = daily_trend

        # 에이전트 통계
        agent_stats = self.monitor.get_agent_stats(days=7)

        if agent_stats:
            total_calls = sum(s["total_calls"] for s in agent_stats.values())
            total_success = sum(s["success_calls"] for s in agent_stats.values())
            total_tokens = sum(s["total_tokens"] for s in agent_stats.values())
            avg_duration = sum(s["avg_duration"] * s["total_calls"] for s in agent_stats.values())
            avg_duration = avg_duration / total_calls if total_calls > 0 else 0

            report["summary"] = {
                "total_calls": total_calls,
                "success_calls": total_success,
                "success_rate": round(total_success / total_calls * 100, 1) if total_calls > 0 else 0,
                "total_tokens": total_tokens,
                "avg_daily_calls": round(total_calls / 7, 1),
                "avg_response_time": round(avg_duration, 2)
            }

            # 상위 에이전트
            sorted_agents = sorted(
                agent_stats.items(),
                key=lambda x: x[1]["total_calls"],
                reverse=True
            )[:5]
            report["top_agents"] = [
                {"name": self._get_agent_name_ko(k), **v}
                for k, v in sorted_agents
            ]

        # 상위 작업 유형
        task_stats = self.monitor.get_task_type_stats(days=7)
        report["top_tasks"] = [
            {"task": k, "count": v}
            for k, v in list(task_stats.items())[:10]
        ]

        # 효율성 메트릭
        if daily_trend:
            avg_success_rate = sum(d["success_rate"] for d in daily_trend) / len(daily_trend)
            report["efficiency_metrics"] = {
                "avg_success_rate": round(avg_success_rate, 1),
                "peak_day": max(daily_trend, key=lambda x: x["total_calls"])["date"] if daily_trend else None,
                "lowest_day": min(daily_trend, key=lambda x: x["total_calls"])["date"] if daily_trend else None
            }

        # 권장사항 생성
        report["recommendations"] = self._generate_recommendations(agent_stats, daily_trend)

        return report

    def generate_monthly_report(self, year: int = None, month: int = None) -> Dict[str, Any]:
        """월간 리포트 생성"""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month

        report = {
            "type": "monthly",
            "period": {
                "year": year,
                "month": month
            },
            "generated_at": datetime.now().isoformat(),
            "summary": {},
            "weekly_breakdown": [],
            "agent_performance": {},
            "trends": {},
            "executive_summary": ""
        }

        # 30일 데이터 기준
        agent_stats = self.monitor.get_agent_stats(days=30)
        daily_trend = self.monitor.get_daily_trend(30)

        if agent_stats:
            total_calls = sum(s["total_calls"] for s in agent_stats.values())
            total_success = sum(s["success_calls"] for s in agent_stats.values())
            total_tokens = sum(s["total_tokens"] for s in agent_stats.values())

            report["summary"] = {
                "total_calls": total_calls,
                "success_calls": total_success,
                "success_rate": round(total_success / total_calls * 100, 1) if total_calls > 0 else 0,
                "total_tokens": total_tokens,
                "avg_daily_calls": round(total_calls / 30, 1),
                "active_agents": len(agent_stats),
                "estimated_time_saved_hours": round(total_calls * 0.5, 1)  # 평균 30분 절약 가정
            }

            report["agent_performance"] = {
                self._get_agent_name_ko(k): {
                    "calls": v["total_calls"],
                    "success_rate": v["success_rate"],
                    "avg_duration": v["avg_duration"],
                    "rank": idx + 1
                }
                for idx, (k, v) in enumerate(
                    sorted(agent_stats.items(), key=lambda x: x[1]["total_calls"], reverse=True)
                )
            }

        # 주차별 분류
        if daily_trend:
            weeks = defaultdict(list)
            for day in daily_trend:
                week_num = datetime.fromisoformat(day["date"]).isocalendar()[1]
                weeks[week_num].append(day)

            for week_num, days in sorted(weeks.items()):
                week_calls = sum(d["total_calls"] for d in days)
                week_success = sum(d["success_calls"] for d in days)
                report["weekly_breakdown"].append({
                    "week": week_num,
                    "total_calls": week_calls,
                    "success_rate": round(week_success / week_calls * 100, 1) if week_calls > 0 else 0
                })

        # 경영진 요약
        report["executive_summary"] = self._generate_executive_summary(report)

        return report

    def _generate_recommendations(
        self,
        agent_stats: Dict[str, Any],
        daily_trend: List[Dict]
    ) -> List[str]:
        """권장사항 생성"""
        recommendations = []

        if not agent_stats:
            return ["데이터가 충분하지 않아 권장사항을 생성할 수 없습니다."]

        # 성공률 낮은 에이전트
        for agent, stats in agent_stats.items():
            if stats["success_rate"] < 90 and stats["total_calls"] >= 5:
                recommendations.append(
                    f"📉 {self._get_agent_name_ko(agent)} 에이전트의 성공률({stats['success_rate']}%)이 "
                    f"목표(90%)보다 낮습니다. 프롬프트 튜닝을 검토하세요."
                )

        # 응답 시간 긴 에이전트
        for agent, stats in agent_stats.items():
            if stats["avg_duration"] > 20:
                recommendations.append(
                    f"⏱️ {self._get_agent_name_ko(agent)} 에이전트의 평균 응답 시간({stats['avg_duration']:.1f}초)이 "
                    f"깁니다. 쿼리 최적화를 고려하세요."
                )

        # 사용량 급변
        if len(daily_trend) >= 7:
            recent_avg = sum(d["total_calls"] for d in daily_trend[-3:]) / 3
            earlier_avg = sum(d["total_calls"] for d in daily_trend[:4]) / 4
            if earlier_avg > 0 and abs(recent_avg - earlier_avg) / earlier_avg > 0.5:
                if recent_avg > earlier_avg:
                    recommendations.append(
                        "📈 최근 사용량이 급증했습니다. 용량 계획을 검토하세요."
                    )
                else:
                    recommendations.append(
                        "📉 최근 사용량이 감소했습니다. 사용자 피드백을 수집해보세요."
                    )

        if not recommendations:
            recommendations.append("✅ 현재 시스템이 정상적으로 운영되고 있습니다.")

        return recommendations

    def _generate_executive_summary(self, report: Dict[str, Any]) -> str:
        """경영진 요약 생성"""
        summary = report.get("summary", {})

        if not summary:
            return "데이터가 충분하지 않습니다."

        text = f"""
## {report['period']['year']}년 {report['period']['month']}월 AI 에이전트 시스템 운영 보고

### 주요 성과
- 월간 총 {summary.get('total_calls', 0):,}건의 업무 처리
- 성공률 {summary.get('success_rate', 0)}% 달성
- 일평균 {summary.get('avg_daily_calls', 0):.1f}건 처리
- 추정 절약 시간: {summary.get('estimated_time_saved_hours', 0):.1f}시간

### 활용 현황
- 활성 에이전트: {summary.get('active_agents', 0)}개
- 총 토큰 사용: {summary.get('total_tokens', 0):,}

### 권장 조치
시스템 안정성 유지 및 사용자 교육 지속 필요.
"""
        return text.strip()

    def format_as_markdown(self, report: Dict[str, Any]) -> str:
        """마크다운 형식으로 변환"""
        report_type = report.get("type", "unknown")

        if report_type == "daily":
            return self._format_daily_markdown(report)
        elif report_type == "weekly":
            return self._format_weekly_markdown(report)
        elif report_type == "monthly":
            return self._format_monthly_markdown(report)

        return json.dumps(report, ensure_ascii=False, indent=2)

    def _format_daily_markdown(self, report: Dict) -> str:
        """일일 리포트 마크다운 형식"""
        summary = report.get("summary", {})

        md = f"""# 📊 일일 리포트 - {report['date']}

## 요약
| 항목 | 값 |
|------|-----|
| 총 호출 | {summary.get('total_calls', 0):,}건 |
| 성공률 | {summary.get('success_rate', 0)}% |
| 토큰 사용 | {summary.get('total_tokens', 0):,} |
| 활성 에이전트 | {summary.get('active_agents', 0)}개 |

## 에이전트별 현황
| 에이전트 | 호출 | 성공률 | 평균시간 |
|----------|------|--------|----------|
"""
        for agent, stats in report.get("agent_breakdown", {}).items():
            md += f"| {agent} | {stats['total_calls']} | {stats['success_rate']}% | {stats['avg_duration']:.1f}s |\n"

        md += f"\n---\n생성: {report['generated_at']}"
        return md

    def _format_weekly_markdown(self, report: Dict) -> str:
        """주간 리포트 마크다운 형식"""
        summary = report.get("summary", {})
        period = report.get("period", {})

        md = f"""# 📊 주간 리포트

**기간**: {period.get('start')} ~ {period.get('end')}

## 요약
| 항목 | 값 |
|------|-----|
| 총 호출 | {summary.get('total_calls', 0):,}건 |
| 성공률 | {summary.get('success_rate', 0)}% |
| 일평균 호출 | {summary.get('avg_daily_calls', 0)}건 |
| 평균 응답시간 | {summary.get('avg_response_time', 0)}초 |

## 일별 추이
| 날짜 | 호출 | 성공률 |
|------|------|--------|
"""
        for day in report.get("daily_trend", []):
            md += f"| {day['date']} | {day['total_calls']} | {day['success_rate']}% |\n"

        md += "\n## 상위 에이전트\n"
        for agent in report.get("top_agents", []):
            md += f"- **{agent['name']}**: {agent['total_calls']}건 (성공률 {agent['success_rate']}%)\n"

        md += "\n## 권장사항\n"
        for rec in report.get("recommendations", []):
            md += f"- {rec}\n"

        return md

    def _format_monthly_markdown(self, report: Dict) -> str:
        """월간 리포트 마크다운 형식"""
        period = report.get("period", {})

        md = f"""# 📊 월간 리포트 - {period.get('year')}년 {period.get('month')}월

{report.get('executive_summary', '')}

## 에이전트 성과 순위
| 순위 | 에이전트 | 호출 | 성공률 |
|------|----------|------|--------|
"""
        for agent, perf in report.get("agent_performance", {}).items():
            md += f"| {perf['rank']} | {agent} | {perf['calls']} | {perf['success_rate']}% |\n"

        md += "\n## 주차별 현황\n"
        for week in report.get("weekly_breakdown", []):
            md += f"- **{week['week']}주차**: {week['total_calls']}건 (성공률 {week['success_rate']}%)\n"

        return md

    def format_as_html(self, report: Dict[str, Any]) -> str:
        """HTML 형식으로 변환"""
        md_content = self.format_as_markdown(report)

        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DSHS AI Agent 리포트</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .summary-box {{ background: #ecf0f1; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px 20px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2980b9; }}
        .metric-label {{ color: #7f8c8d; }}
    </style>
</head>
<body>
    <pre style="white-space: pre-wrap;">{md_content}</pre>
</body>
</html>"""
        return html


def main():
    parser = argparse.ArgumentParser(
        description="DSHS AI Agent 사용 통계 리포트 생성"
    )
    parser.add_argument("--daily", "-d", action="store_true", help="일일 리포트")
    parser.add_argument("--weekly", "-w", action="store_true", help="주간 리포트")
    parser.add_argument("--monthly", "-m", action="store_true", help="월간 리포트")
    parser.add_argument("--format", "-f", choices=["json", "markdown", "html"], default="markdown", help="출력 형식")
    parser.add_argument("--output", "-o", help="출력 파일 경로")

    args = parser.parse_args()

    generator = ReportGenerator()

    # 리포트 생성
    if args.daily:
        report = generator.generate_daily_report()
    elif args.weekly:
        report = generator.generate_weekly_report()
    elif args.monthly:
        report = generator.generate_monthly_report()
    else:
        # 기본: 주간 리포트
        report = generator.generate_weekly_report()

    # 형식 변환
    if args.format == "json":
        output = json.dumps(report, ensure_ascii=False, indent=2)
        ext = ".json"
    elif args.format == "html":
        output = generator.format_as_html(report)
        ext = ".html"
    else:
        output = generator.format_as_markdown(report)
        ext = ".md"

    # 출력
    if args.output:
        output_path = args.output if "." in args.output else args.output + ext
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"✅ 리포트 저장: {output_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
