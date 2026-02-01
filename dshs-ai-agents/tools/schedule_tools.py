# DSHS AI Agent System - Schedule Tools
# 대전과학고등학교 AI 에이전트 시스템 - 일정 관리 도구

"""
학사일정, 시간표, 연구 일정 등을 관리하는 도구
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class EventType(Enum):
    """일정 유형"""
    EXAM = "정기고사"
    RESEARCH = "자율연구"
    CEREMONY = "행사/식전"
    VACATION = "방학"
    COMPETITION = "대회"
    FIELD_TRIP = "체험학습"
    MEETING = "회의"
    DEADLINE = "마감"
    OTHER = "기타"


class ConflictLevel(Enum):
    """충돌 수준"""
    NONE = "없음"
    LOW = "경미"
    MEDIUM = "조정필요"
    HIGH = "심각"
    CRITICAL = "불가"


@dataclass
class ScheduleEvent:
    """일정 이벤트"""
    id: str
    title: str
    event_type: EventType
    start_date: datetime
    end_date: datetime
    departments: List[str]
    priority: int = 5  # 1-10, 높을수록 중요
    description: str = ""
    location: str = ""
    participants: List[str] = field(default_factory=list)
    is_fixed: bool = False  # 변경 불가 일정


@dataclass
class ConflictReport:
    """충돌 보고서"""
    event1: ScheduleEvent
    event2: ScheduleEvent
    conflict_level: ConflictLevel
    overlap_days: int
    suggestion: str


class ScheduleTools:
    """일정 관리 도구 클래스"""

    # 학사일정 기본 템플릿 (2026학년도 기준)
    ACADEMIC_CALENDAR_2026 = {
        "1학기": {
            "시작": "2026-03-02",
            "종료": "2026-07-17",
            "중간고사": ("2026-04-20", "2026-04-24"),
            "기말고사": ("2026-07-06", "2026-07-10"),
            "여름방학": ("2026-07-18", "2026-08-21"),
        },
        "2학기": {
            "시작": "2026-08-24",
            "종료": "2027-02-12",
            "중간고사": ("2026-10-12", "2026-10-16"),
            "기말고사": ("2026-12-14", "2026-12-18"),
            "겨울방학": ("2026-12-24", "2027-02-11"),
        }
    }

    # 자율연구 주요 일정
    RESEARCH_MILESTONES = {
        "기초연구": {
            "팀구성": "3월 2주",
            "계획서": "3월 4주",
            "중간발표": "6월 2주",
            "최종발표": "7월 1주",
        },
        "심화연구": {
            "팀구성": "3월 2주",
            "계획서": "3월 4주",
            "중간발표": "6월 2주",
            "최종발표": "12월 2주",
        },
        "졸업논문": {
            "주제확정": "3월 4주",
            "계획발표": "4월 3주",
            "중간발표": "9월 2주",
            "논문제출": "11월 4주",
            "구술시험": "12월 2주",
        }
    }

    @classmethod
    def check_conflicts(
        cls,
        new_event: ScheduleEvent,
        existing_events: List[ScheduleEvent]
    ) -> List[ConflictReport]:
        """
        새 일정과 기존 일정 간 충돌 확인

        Args:
            new_event: 추가하려는 새 일정
            existing_events: 기존 일정 목록

        Returns:
            충돌 보고서 목록
        """
        conflicts = []

        for existing in existing_events:
            overlap = cls._calculate_overlap(new_event, existing)
            if overlap > 0:
                level = cls._assess_conflict_level(new_event, existing, overlap)
                suggestion = cls._generate_suggestion(new_event, existing, level)

                conflicts.append(ConflictReport(
                    event1=new_event,
                    event2=existing,
                    conflict_level=level,
                    overlap_days=overlap,
                    suggestion=suggestion
                ))

        return conflicts

    @classmethod
    def generate_research_schedule(
        cls,
        research_type: str,
        start_date: str,
        team_count: int = 1
    ) -> Dict[str, Any]:
        """
        자율연구 일정 자동 생성

        Args:
            research_type: 연구 유형 (기초연구, 심화연구, 졸업논문)
            start_date: 시작일 (YYYY-MM-DD)
            team_count: 팀 수 (구술시험 일정 산정용)
        """
        if research_type not in cls.RESEARCH_MILESTONES:
            return {
                "success": False,
                "error": f"알 수 없는 연구 유형: {research_type}"
            }

        milestones = cls.RESEARCH_MILESTONES[research_type]
        start = datetime.strptime(start_date, "%Y-%m-%d")

        schedule = []
        for milestone, timing in milestones.items():
            # 실제 날짜 계산 (간략화된 버전)
            schedule.append({
                "milestone": milestone,
                "timing": timing,
                "description": f"{research_type} - {milestone}"
            })

        # 구술시험 세부 일정 (졸업논문인 경우)
        if research_type == "졸업논문" and team_count > 0:
            oral_exam_schedule = cls._generate_oral_exam_slots(team_count)
            schedule.append({
                "milestone": "구술시험_상세",
                "slots": oral_exam_schedule
            })

        return {
            "success": True,
            "research_type": research_type,
            "schedule": schedule,
            "team_count": team_count
        }

    @classmethod
    def optimize_exam_schedule(
        cls,
        subjects: List[str],
        exam_days: int,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        시험 시간표 최적화

        Args:
            subjects: 시험 과목 목록
            exam_days: 시험 기간 (일)
            constraints: 제약조건 (연속 금지 과목, 필수 간격 등)
        """
        constraints = constraints or {}

        # 기본 규칙
        max_subjects_per_day = 3
        min_prep_time_hours = 16  # 최소 준비 시간

        # 간단한 스케줄링 (실제로는 더 복잡한 최적화 필요)
        schedule = []
        subjects_per_day = min(max_subjects_per_day, len(subjects) // exam_days + 1)

        for day in range(exam_days):
            day_subjects = subjects[day * subjects_per_day:(day + 1) * subjects_per_day]
            if day_subjects:
                schedule.append({
                    "day": day + 1,
                    "subjects": day_subjects
                })

        return {
            "success": True,
            "exam_days": exam_days,
            "schedule": schedule,
            "subjects_count": len(subjects),
            "note": "실제 적용 전 교육과정부 검토 필요"
        }

    @classmethod
    def get_academic_calendar(
        cls,
        year: int = 2026,
        semester: Optional[int] = None
    ) -> Dict[str, Any]:
        """학사일정 조회"""
        if semester:
            key = f"{semester}학기"
            if key in cls.ACADEMIC_CALENDAR_2026:
                return {
                    "success": True,
                    "year": year,
                    "semester": semester,
                    "calendar": cls.ACADEMIC_CALENDAR_2026[key]
                }
        return {
            "success": True,
            "year": year,
            "calendar": cls.ACADEMIC_CALENDAR_2026
        }

    @classmethod
    def calculate_working_days(
        cls,
        start_date: str,
        end_date: str,
        exclude_holidays: bool = True
    ) -> Dict[str, Any]:
        """
        근무일수 계산

        Args:
            start_date: 시작일
            end_date: 종료일
            exclude_holidays: 공휴일 제외 여부
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        total_days = (end - start).days + 1
        weekends = sum(1 for i in range(total_days)
                      if (start + timedelta(days=i)).weekday() >= 5)

        working_days = total_days - weekends

        # 공휴일은 별도 데이터 필요 (여기서는 대략적 추정)
        estimated_holidays = total_days // 30  # 월당 약 1일

        if exclude_holidays:
            working_days -= estimated_holidays

        return {
            "success": True,
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "weekends": weekends,
            "estimated_holidays": estimated_holidays,
            "working_days": working_days
        }

    @staticmethod
    def _calculate_overlap(event1: ScheduleEvent, event2: ScheduleEvent) -> int:
        """두 일정의 겹치는 일수 계산"""
        latest_start = max(event1.start_date, event2.start_date)
        earliest_end = min(event1.end_date, event2.end_date)
        delta = (earliest_end - latest_start).days + 1
        return max(0, delta)

    @staticmethod
    def _assess_conflict_level(
        event1: ScheduleEvent,
        event2: ScheduleEvent,
        overlap: int
    ) -> ConflictLevel:
        """충돌 수준 평가"""
        # 고정 일정과 충돌
        if event1.is_fixed or event2.is_fixed:
            return ConflictLevel.CRITICAL

        # 같은 부서
        common_depts = set(event1.departments) & set(event2.departments)
        if common_depts:
            if overlap >= 3:
                return ConflictLevel.HIGH
            return ConflictLevel.MEDIUM

        # 다른 부서지만 겹침
        if overlap >= 5:
            return ConflictLevel.MEDIUM
        elif overlap >= 1:
            return ConflictLevel.LOW

        return ConflictLevel.NONE

    @staticmethod
    def _generate_suggestion(
        event1: ScheduleEvent,
        event2: ScheduleEvent,
        level: ConflictLevel
    ) -> str:
        """충돌 해결 제안 생성"""
        if level == ConflictLevel.CRITICAL:
            return f"'{event2.title}'은(는) 고정 일정입니다. '{event1.title}'의 일정을 조정하세요."
        elif level == ConflictLevel.HIGH:
            return f"'{event1.title}'을(를) 1주 이상 앞당기거나 뒤로 미루는 것을 권장합니다."
        elif level == ConflictLevel.MEDIUM:
            return f"관련 부서 간 협의를 통해 일정을 조정하세요."
        elif level == ConflictLevel.LOW:
            return f"일정이 일부 겹치지만 진행 가능합니다. 참여자 조정을 고려하세요."
        return "충돌 없음"

    @staticmethod
    def _generate_oral_exam_slots(team_count: int) -> List[Dict[str, Any]]:
        """구술시험 시간표 슬롯 생성"""
        slots_per_day = 12  # 하루 최대 12팀
        exam_duration = 30  # 분
        break_duration = 10  # 분

        days_needed = (team_count + slots_per_day - 1) // slots_per_day

        schedule = []
        for day in range(days_needed):
            day_teams = min(slots_per_day, team_count - day * slots_per_day)
            slots = []
            start_time = 9 * 60  # 9:00 AM in minutes

            for i in range(day_teams):
                start_h, start_m = divmod(start_time, 60)
                end_time = start_time + exam_duration
                end_h, end_m = divmod(end_time, 60)

                slots.append({
                    "slot": i + 1,
                    "time": f"{start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}",
                    "team": f"팀 {day * slots_per_day + i + 1}"
                })

                start_time = end_time + break_duration

                # 점심시간 (12:00-13:00)
                if start_time >= 12 * 60 and start_time < 13 * 60:
                    start_time = 13 * 60

            schedule.append({
                "day": day + 1,
                "slots": slots
            })

        return schedule


# 편의 함수들
def check_schedule_conflict(
    title: str,
    start: str,
    end: str,
    event_type: str = "OTHER"
) -> Dict[str, Any]:
    """일정 충돌 간편 확인"""
    # 실제로는 기존 일정 데이터베이스 조회 필요
    return {
        "success": True,
        "event": title,
        "period": f"{start} ~ {end}",
        "conflicts": [],
        "message": "기존 일정 데이터 연동 필요"
    }


def get_research_timeline(research_type: str) -> Dict[str, Any]:
    """자율연구 타임라인 조회"""
    return ScheduleTools.generate_research_schedule(
        research_type=research_type,
        start_date=datetime.now().strftime("%Y-%m-%d")
    )


def get_exam_period(semester: int) -> Dict[str, Any]:
    """시험 기간 조회"""
    calendar = ScheduleTools.get_academic_calendar(semester=semester)
    if calendar["success"]:
        return {
            "중간고사": calendar["calendar"].get("중간고사"),
            "기말고사": calendar["calendar"].get("기말고사")
        }
    return calendar
