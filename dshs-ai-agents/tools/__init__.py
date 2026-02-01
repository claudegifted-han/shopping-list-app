# DSHS AI Agent System - Tools Package
# 대전과학고등학교 AI 에이전트 시스템 - 도구 패키지

"""
AI 에이전트 도구 모음

Available tools:
- notion_tools: Notion MCP 연동
- doc_generator: 문서 생성
- schedule_tools: 일정 관리
- neis_helper: NEIS 기재 지원
- statistics_tools: 통계 분석
"""

from .notion_tools import (
    NotionTools,
    NotionDBType,
    search_students,
    search_research,
    get_upcoming_events,
    create_document_record,
)

from .doc_generator import (
    DocGenerator,
    DocType,
    DocumentMetadata,
    create_official_doc,
    create_home_letter,
    create_neis_record,
)

from .schedule_tools import (
    ScheduleTools,
    EventType,
    ScheduleEvent,
    check_schedule_conflict,
    get_research_timeline,
    get_exam_period,
)

from .neis_helper import (
    NEISHelper,
    NEISSection,
    validate_research_record,
    create_research_record,
    get_char_limit,
)

from .statistics_tools import (
    StatisticsTools,
    StatType,
    analyze_scores,
    analyze_projects,
    compare_periods,
    format_table,
)

__version__ = "2.0.0"
__all__ = [
    # Notion
    "NotionTools",
    "NotionDBType",
    "search_students",
    "search_research",
    "get_upcoming_events",
    "create_document_record",
    # Document Generator
    "DocGenerator",
    "DocType",
    "DocumentMetadata",
    "create_official_doc",
    "create_home_letter",
    "create_neis_record",
    # Schedule
    "ScheduleTools",
    "EventType",
    "ScheduleEvent",
    "check_schedule_conflict",
    "get_research_timeline",
    "get_exam_period",
    # NEIS
    "NEISHelper",
    "NEISSection",
    "validate_research_record",
    "create_research_record",
    "get_char_limit",
    # Statistics
    "StatisticsTools",
    "StatType",
    "analyze_scores",
    "analyze_projects",
    "compare_periods",
    "format_table",
]
