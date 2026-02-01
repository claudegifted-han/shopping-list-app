# DSHS AI Agent System - Statistics Tools
# 대전과학고등학교 AI 에이전트 시스템 - 통계 분석 도구

"""
성적, 연구, 행사 등 각종 통계 분석 도구
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import Counter
import math


class StatType(Enum):
    """통계 유형"""
    GRADE = "성적"
    RESEARCH = "연구"
    ATTENDANCE = "출석"
    EVENT = "행사"
    ADMISSION = "입학"
    CLUB = "동아리"


@dataclass
class StatsSummary:
    """통계 요약"""
    count: int
    mean: float
    median: float
    std_dev: float
    min_val: float
    max_val: float
    quartiles: Tuple[float, float, float]


class StatisticsTools:
    """통계 분석 도구 클래스"""

    @staticmethod
    def calculate_basic_stats(values: List[float]) -> StatsSummary:
        """
        기본 통계량 계산

        Args:
            values: 수치 데이터 목록

        Returns:
            통계 요약
        """
        if not values:
            return StatsSummary(0, 0, 0, 0, 0, 0, (0, 0, 0))

        n = len(values)
        sorted_vals = sorted(values)

        # 평균
        mean = sum(values) / n

        # 중앙값
        if n % 2 == 0:
            median = (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
        else:
            median = sorted_vals[n//2]

        # 표준편차
        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = math.sqrt(variance)

        # 사분위수
        q1 = sorted_vals[n//4]
        q2 = median
        q3 = sorted_vals[3*n//4]

        return StatsSummary(
            count=n,
            mean=round(mean, 2),
            median=round(median, 2),
            std_dev=round(std_dev, 2),
            min_val=min(values),
            max_val=max(values),
            quartiles=(round(q1, 2), round(q2, 2), round(q3, 2))
        )

    @classmethod
    def analyze_grade_distribution(
        cls,
        scores: List[float],
        subject: str = "",
        exam_type: str = ""
    ) -> Dict[str, Any]:
        """
        성적 분포 분석

        Args:
            scores: 점수 목록
            subject: 과목명
            exam_type: 시험 유형 (중간/기말)
        """
        if not scores:
            return {"success": False, "error": "데이터 없음"}

        stats = cls.calculate_basic_stats(scores)

        # 등급 분포 (상대평가 기준)
        sorted_scores = sorted(scores, reverse=True)
        n = len(scores)
        grade_cuts = {
            "A": int(n * 0.1),
            "B": int(n * 0.34),
            "C": int(n * 0.66),
            "D": int(n * 0.9),
            "E": n
        }

        grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
        grade_cutoffs = {}

        prev_cut = 0
        for grade, cut in grade_cuts.items():
            grade_distribution[grade] = cut - prev_cut
            if cut > 0 and cut <= n:
                grade_cutoffs[grade] = sorted_scores[cut - 1] if cut <= n else 0
            prev_cut = cut

        # 점수대별 분포
        score_ranges = {
            "90-100": 0,
            "80-89": 0,
            "70-79": 0,
            "60-69": 0,
            "0-59": 0
        }
        for score in scores:
            if score >= 90:
                score_ranges["90-100"] += 1
            elif score >= 80:
                score_ranges["80-89"] += 1
            elif score >= 70:
                score_ranges["70-79"] += 1
            elif score >= 60:
                score_ranges["60-69"] += 1
            else:
                score_ranges["0-59"] += 1

        return {
            "success": True,
            "subject": subject,
            "exam_type": exam_type,
            "statistics": {
                "count": stats.count,
                "mean": stats.mean,
                "median": stats.median,
                "std_dev": stats.std_dev,
                "min": stats.min_val,
                "max": stats.max_val,
                "quartiles": {
                    "Q1": stats.quartiles[0],
                    "Q2": stats.quartiles[1],
                    "Q3": stats.quartiles[2]
                }
            },
            "grade_distribution": grade_distribution,
            "grade_cutoffs": grade_cutoffs,
            "score_ranges": score_ranges
        }

    @classmethod
    def analyze_research_statistics(
        cls,
        projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        자율연구 통계 분석

        Args:
            projects: 연구 프로젝트 목록
                [{"type": "", "status": "", "grade": 1, "field": "", "team_size": 2}]
        """
        if not projects:
            return {"success": False, "error": "데이터 없음"}

        # 유형별 분포
        type_dist = Counter(p.get("type", "기타") for p in projects)

        # 상태별 분포
        status_dist = Counter(p.get("status", "진행중") for p in projects)

        # 학년별 분포
        grade_dist = Counter(p.get("grade", 0) for p in projects)

        # 분야별 분포
        field_dist = Counter(p.get("field", "기타") for p in projects)

        # 팀 규모 분석
        team_sizes = [p.get("team_size", 1) for p in projects]
        team_stats = cls.calculate_basic_stats([float(t) for t in team_sizes])

        return {
            "success": True,
            "total_projects": len(projects),
            "by_type": dict(type_dist),
            "by_status": dict(status_dist),
            "by_grade": dict(grade_dist),
            "by_field": dict(field_dist),
            "team_size": {
                "average": team_stats.mean,
                "min": int(team_stats.min_val),
                "max": int(team_stats.max_val)
            }
        }

    @classmethod
    def analyze_attendance(
        cls,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        출결 통계 분석

        Args:
            records: 출결 기록
                [{"student_id": "", "date": "", "status": "출석/지각/조퇴/결석"}]
        """
        if not records:
            return {"success": False, "error": "데이터 없음"}

        status_dist = Counter(r.get("status", "출석") for r in records)

        total = len(records)
        attendance_rate = (status_dist.get("출석", 0) / total * 100) if total > 0 else 0

        # 학생별 출결
        student_records = {}
        for record in records:
            sid = record.get("student_id", "")
            if sid not in student_records:
                student_records[sid] = {"출석": 0, "지각": 0, "조퇴": 0, "결석": 0}
            status = record.get("status", "출석")
            if status in student_records[sid]:
                student_records[sid][status] += 1

        # 출결 우려 학생 (결석 3회 이상 또는 지각 5회 이상)
        concern_students = [
            sid for sid, stats in student_records.items()
            if stats.get("결석", 0) >= 3 or stats.get("지각", 0) >= 5
        ]

        return {
            "success": True,
            "total_records": total,
            "status_distribution": dict(status_dist),
            "attendance_rate": round(attendance_rate, 1),
            "student_count": len(student_records),
            "concern_students_count": len(concern_students),
            "concern_students": concern_students[:10]  # 상위 10명만
        }

    @classmethod
    def analyze_event_participation(
        cls,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        행사 참여 통계

        Args:
            events: 행사 기록
                [{"event_name": "", "date": "", "participants": 100, "type": ""}]
        """
        if not events:
            return {"success": False, "error": "데이터 없음"}

        # 행사 유형별 분포
        type_dist = Counter(e.get("type", "기타") for e in events)

        # 참여자 수 분석
        participant_counts = [e.get("participants", 0) for e in events]
        participant_stats = cls.calculate_basic_stats([float(p) for p in participant_counts])

        # 월별 행사 분포
        month_dist = Counter()
        for event in events:
            date_str = event.get("date", "")
            if len(date_str) >= 7:  # YYYY-MM 형식
                month = date_str[:7]
                month_dist[month] += 1

        return {
            "success": True,
            "total_events": len(events),
            "by_type": dict(type_dist),
            "by_month": dict(sorted(month_dist.items())),
            "participation": {
                "total": sum(participant_counts),
                "average": participant_stats.mean,
                "min": int(participant_stats.min_val),
                "max": int(participant_stats.max_val)
            }
        }

    @classmethod
    def generate_comparison_report(
        cls,
        current: Dict[str, Any],
        previous: Dict[str, Any],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """
        비교 분석 보고서 생성

        Args:
            current: 현재 기간 데이터
            previous: 이전 기간 데이터
            metrics: 비교할 지표 목록
        """
        comparisons = []

        for metric in metrics:
            curr_val = current.get(metric, 0)
            prev_val = previous.get(metric, 0)

            if prev_val != 0:
                change_rate = ((curr_val - prev_val) / prev_val) * 100
            else:
                change_rate = 100 if curr_val > 0 else 0

            comparisons.append({
                "metric": metric,
                "current": curr_val,
                "previous": prev_val,
                "change": curr_val - prev_val,
                "change_rate": round(change_rate, 1),
                "trend": "↑" if change_rate > 0 else "↓" if change_rate < 0 else "→"
            })

        return {
            "success": True,
            "comparisons": comparisons,
            "summary": {
                "improved": sum(1 for c in comparisons if c["change_rate"] > 0),
                "declined": sum(1 for c in comparisons if c["change_rate"] < 0),
                "stable": sum(1 for c in comparisons if c["change_rate"] == 0)
            }
        }

    @classmethod
    def format_statistics_table(
        cls,
        data: Dict[str, Any],
        title: str = "통계 현황"
    ) -> str:
        """
        통계 데이터를 표 형식으로 포맷팅
        """
        lines = [
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"  {title}",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"\n【{key}】")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            else:
                lines.append(f"  {key}: {value}")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)


# 편의 함수들
def analyze_scores(scores: List[float], subject: str = "") -> Dict[str, Any]:
    """점수 분석 간편 함수"""
    return StatisticsTools.analyze_grade_distribution(scores, subject)


def analyze_projects(projects: List[Dict]) -> Dict[str, Any]:
    """프로젝트 분석 간편 함수"""
    return StatisticsTools.analyze_research_statistics(projects)


def compare_periods(current: Dict, previous: Dict, metrics: List[str]) -> Dict[str, Any]:
    """기간 비교 간편 함수"""
    return StatisticsTools.generate_comparison_report(current, previous, metrics)


def format_table(data: Dict, title: str = "통계") -> str:
    """표 포맷팅 간편 함수"""
    return StatisticsTools.format_statistics_table(data, title)
