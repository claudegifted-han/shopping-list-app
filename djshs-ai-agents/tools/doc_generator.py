# DJSHS AI Agent System - Document Generator
# 대전과학고등학교 AI 에이전트 시스템 - 문서 생성 도구

"""
템플릿 기반 문서 생성 도구
공문, 보고서, 가정통신문 등을 템플릿에서 생성합니다.
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class DocType(Enum):
    """문서 유형"""
    # 공문/서신
    OFFICIAL_DOCUMENT = "letters/official_document"
    HOME_LETTER = "letters/home_letter"
    RNE_ANNOUNCEMENT = "letters/rne_announcement"

    # 보고서
    RESEARCH_PLAN = "reports/research_plan"
    RESEARCH_REPORT = "reports/research_report"
    ORAL_EXAM_SCHEDULE = "reports/oral_exam_schedule"
    MEETING_MINUTES = "reports/meeting_minutes"
    EVENT_PLAN = "reports/event_plan"
    STATISTICS_REPORT = "reports/statistics_report"
    BRAINSTORM_REPORT = "reports/brainstorm_report"
    POLICY_ANALYSIS = "reports/policy_analysis"
    RISK_ASSESSMENT = "reports/risk_assessment"

    # NEIS 기재
    NEIS_RESEARCH = "neis/autonomous_research"


@dataclass
class DocumentMetadata:
    """문서 메타데이터"""
    title: str
    doc_type: DocType
    author_department: str
    created_at: str
    version: str = "1.0"
    status: str = "draft"  # draft, review, final
    security_level: str = "일반"


class DocGenerator:
    """문서 생성기 클래스"""

    TEMPLATE_BASE = Path(__file__).parent.parent / "templates"

    @classmethod
    def generate(
        cls,
        doc_type: DocType,
        variables: Dict[str, Any],
        metadata: Optional[DocumentMetadata] = None
    ) -> Dict[str, Any]:
        """
        템플릿에서 문서 생성

        Args:
            doc_type: 문서 유형
            variables: 템플릿 변수
            metadata: 문서 메타데이터

        Returns:
            생성된 문서 정보
        """
        template_path = cls.TEMPLATE_BASE / f"{doc_type.value}.md"

        # 템플릿 로드
        if not template_path.exists():
            return {
                "success": False,
                "error": f"템플릿 없음: {template_path}"
            }

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # 변수 치환
        content = cls._substitute_variables(template, variables)

        # 메타데이터 추가
        if metadata:
            content = cls._add_metadata_header(content, metadata)

        return {
            "success": True,
            "doc_type": doc_type.value,
            "content": content,
            "metadata": metadata.__dict__ if metadata else None,
            "generated_at": datetime.now().isoformat()
        }

    @classmethod
    def generate_official_document(
        cls,
        doc_number: str,
        recipient: str,
        title: str,
        body: str,
        attachments: Optional[List[str]] = None,
        department: str = "교무운영부"
    ) -> Dict[str, Any]:
        """
        공문 생성

        Args:
            doc_number: 문서번호 (예: 2026-001)
            recipient: 수신처
            title: 제목
            body: 본문
            attachments: 첨부 목록
            department: 작성 부서
        """
        variables = {
            "문서번호": f"대전과학고-{doc_number}",
            "수신": recipient,
            "제목": title,
            "본문": body,
            "첨부": "\n".join(attachments) if attachments else "없음",
            "시행일": datetime.now().strftime("%Y.%m.%d"),
            "작성부서": department
        }

        metadata = DocumentMetadata(
            title=title,
            doc_type=DocType.OFFICIAL_DOCUMENT,
            author_department=department,
            created_at=datetime.now().isoformat()
        )

        return cls.generate(DocType.OFFICIAL_DOCUMENT, variables, metadata)

    @classmethod
    def generate_home_letter(
        cls,
        title: str,
        greeting: str,
        body: str,
        action_items: List[str],
        deadline: Optional[str] = None,
        contact: str = "교무실 042-863-7801",
        department: str = "교무운영부"
    ) -> Dict[str, Any]:
        """
        가정통신문 생성

        Args:
            title: 제목
            greeting: 인사말
            body: 본문
            action_items: 안내사항 목록
            deadline: 회신 기한
            contact: 연락처
            department: 작성 부서
        """
        variables = {
            "제목": title,
            "인사말": greeting,
            "본문": body,
            "안내사항": "\n".join(f"- {item}" for item in action_items),
            "회신기한": deadline or "별도 안내",
            "연락처": contact,
            "발송일": datetime.now().strftime("%Y년 %m월 %d일")
        }

        metadata = DocumentMetadata(
            title=title,
            doc_type=DocType.HOME_LETTER,
            author_department=department,
            created_at=datetime.now().isoformat()
        )

        return cls.generate(DocType.HOME_LETTER, variables, metadata)

    @classmethod
    def generate_meeting_minutes(
        cls,
        meeting_name: str,
        date: str,
        location: str,
        attendees: List[str],
        agenda: List[Dict[str, str]],
        decisions: List[str],
        action_items: List[Dict[str, str]],
        department: str = "교무운영부"
    ) -> Dict[str, Any]:
        """
        회의록 생성

        Args:
            meeting_name: 회의명
            date: 일시
            location: 장소
            attendees: 참석자 목록
            agenda: 안건 목록 [{"안건": "", "논의": "", "결과": ""}]
            decisions: 의결사항
            action_items: 후속조치 [{"조치": "", "담당": "", "기한": ""}]
            department: 작성 부서
        """
        # 안건 포맷팅
        agenda_text = ""
        for i, item in enumerate(agenda, 1):
            agenda_text += f"\n### 안건 {i}: {item.get('안건', '')}\n"
            agenda_text += f"- 논의 내용: {item.get('논의', '')}\n"
            agenda_text += f"- 결과: {item.get('결과', '')}\n"

        # 후속조치 포맷팅
        action_text = "\n".join(
            f"| {item.get('조치', '')} | {item.get('담당', '')} | {item.get('기한', '')} |"
            for item in action_items
        )

        variables = {
            "회의명": meeting_name,
            "일시": date,
            "장소": location,
            "참석자": ", ".join(attendees),
            "안건": agenda_text,
            "의결사항": "\n".join(f"- {d}" for d in decisions),
            "후속조치": action_text,
            "작성자": department,
            "작성일": datetime.now().strftime("%Y.%m.%d")
        }

        metadata = DocumentMetadata(
            title=meeting_name,
            doc_type=DocType.MEETING_MINUTES,
            author_department=department,
            created_at=datetime.now().isoformat()
        )

        return cls.generate(DocType.MEETING_MINUTES, variables, metadata)

    @classmethod
    def generate_research_plan(
        cls,
        project_title: str,
        student_name: str,
        grade: int,
        advisor: str,
        research_type: str,
        background: str,
        objectives: List[str],
        methodology: str,
        schedule: List[Dict[str, str]],
        expected_outcomes: List[str]
    ) -> Dict[str, Any]:
        """
        자율연구 계획서 생성
        """
        variables = {
            "연구제목": project_title,
            "학생명": student_name,
            "학년": f"{grade}학년",
            "지도교사": advisor,
            "연구유형": research_type,
            "연구배경": background,
            "연구목표": "\n".join(f"{i}. {obj}" for i, obj in enumerate(objectives, 1)),
            "연구방법": methodology,
            "연구일정": "\n".join(
                f"| {s.get('기간', '')} | {s.get('내용', '')} |"
                for s in schedule
            ),
            "기대성과": "\n".join(f"- {o}" for o in expected_outcomes),
            "작성일": datetime.now().strftime("%Y.%m.%d")
        }

        metadata = DocumentMetadata(
            title=project_title,
            doc_type=DocType.RESEARCH_PLAN,
            author_department="영재교육부",
            created_at=datetime.now().isoformat()
        )

        return cls.generate(DocType.RESEARCH_PLAN, variables, metadata)

    @classmethod
    def generate_neis_research_record(
        cls,
        student_name: str,
        grade: int,
        research_title: str,
        research_period: str,
        research_content: str,
        evaluation: str
    ) -> Dict[str, Any]:
        """
        NEIS 자율연구 기재용 텍스트 생성

        Args:
            student_name: 학생명
            grade: 학년
            research_title: 연구 제목
            research_period: 연구 기간
            research_content: 연구 내용 (300자 이내)
            evaluation: 평가 소견 (200자 이내)
        """
        # 글자 수 확인
        if len(research_content) > 300:
            research_content = research_content[:297] + "..."
        if len(evaluation) > 200:
            evaluation = evaluation[:197] + "..."

        variables = {
            "학생명": student_name,
            "학년": grade,
            "연구제목": research_title,
            "연구기간": research_period,
            "연구내용": research_content,
            "평가소견": evaluation,
            "글자수_내용": len(research_content),
            "글자수_평가": len(evaluation)
        }

        return cls.generate(DocType.NEIS_RESEARCH, variables)

    @staticmethod
    def _substitute_variables(template: str, variables: Dict[str, Any]) -> str:
        """템플릿 변수 치환"""
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"  # {{key}} 형식
            if placeholder in result:
                result = result.replace(placeholder, str(value))
            # [key] 형식도 지원
            bracket_placeholder = f"[{key}]"
            if bracket_placeholder in result:
                result = result.replace(bracket_placeholder, str(value))
        return result

    @staticmethod
    def _add_metadata_header(content: str, metadata: DocumentMetadata) -> str:
        """메타데이터 헤더 추가"""
        header = f"""---
title: {metadata.title}
type: {metadata.doc_type.value}
department: {metadata.author_department}
created: {metadata.created_at}
version: {metadata.version}
status: {metadata.status}
security: {metadata.security_level}
---

"""
        return header + content


# 편의 함수들
def create_official_doc(recipient: str, title: str, body: str) -> Dict[str, Any]:
    """공문 간편 생성"""
    doc_number = datetime.now().strftime("%Y-%m%d-%H%M")
    return DocGenerator.generate_official_document(
        doc_number=doc_number,
        recipient=recipient,
        title=title,
        body=body
    )


def create_home_letter(title: str, body: str, items: List[str]) -> Dict[str, Any]:
    """가정통신문 간편 생성"""
    return DocGenerator.generate_home_letter(
        title=title,
        greeting="안녕하십니까? 학부모님의 가정에 건강과 행복이 함께하시길 기원합니다.",
        body=body,
        action_items=items
    )


def create_neis_record(name: str, grade: int, title: str, content: str) -> Dict[str, Any]:
    """NEIS 기재 간편 생성"""
    return DocGenerator.generate_neis_research_record(
        student_name=name,
        grade=grade,
        research_title=title,
        research_period=f"{datetime.now().year}학년도",
        research_content=content,
        evaluation="연구 수행 과정에서 성실한 태도와 창의적 문제해결력을 보임."
    )
