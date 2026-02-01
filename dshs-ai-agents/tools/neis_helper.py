# DSHS AI Agent System - NEIS Helper
# 대전과학고등학교 AI 에이전트 시스템 - NEIS 기재 도우미

"""
NEIS(교육행정정보시스템) 기재 지원 도구
교육부 학생부 기재요령에 따른 텍스트 생성 및 검증
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re


class NEISSection(Enum):
    """NEIS 학생부 영역"""
    AUTONOMOUS_RESEARCH = "자율탐구활동"       # 창의적 체험활동 - 자율활동
    CLUB_ACTIVITY = "동아리활동"               # 창의적 체험활동 - 동아리활동
    VOLUNTEER = "봉사활동"                     # 창의적 체험활동 - 봉사활동
    CAREER = "진로활동"                        # 창의적 체험활동 - 진로활동
    SUBJECT_ACHIEVEMENT = "교과세부능력특기사항"  # 교과학습발달상황
    BEHAVIOR = "행동특성종합의견"               # 행동특성 및 종합의견
    READING = "독서활동"                       # 독서활동상황


@dataclass
class NEISCharLimit:
    """NEIS 글자 수 제한"""
    section: NEISSection
    max_chars: int
    recommended_chars: int


class NEISHelper:
    """NEIS 기재 도우미 클래스"""

    # 영역별 글자 수 제한 (2024 기재요령 기준)
    CHAR_LIMITS = {
        NEISSection.AUTONOMOUS_RESEARCH: NEISCharLimit(NEISSection.AUTONOMOUS_RESEARCH, 500, 400),
        NEISSection.CLUB_ACTIVITY: NEISCharLimit(NEISSection.CLUB_ACTIVITY, 500, 400),
        NEISSection.VOLUNTEER: NEISCharLimit(NEISSection.VOLUNTEER, 500, 400),
        NEISSection.CAREER: NEISCharLimit(NEISSection.CAREER, 700, 500),
        NEISSection.SUBJECT_ACHIEVEMENT: NEISCharLimit(NEISSection.SUBJECT_ACHIEVEMENT, 500, 400),
        NEISSection.BEHAVIOR: NEISCharLimit(NEISSection.BEHAVIOR, 500, 400),
        NEISSection.READING: NEISCharLimit(NEISSection.READING, 500, 400),
    }

    # 금지 표현
    PROHIBITED_EXPRESSIONS = [
        # 순위/등급 관련
        r'\d+등', r'최우수', r'우수', r'최고',
        # 외부 대회
        r'올림피아드', r'경시대회', r'전국대회', r'과학전람회',
        # 인증/자격
        r'토익', r'토플', r'텝스', r'자격증', r'급수',
        # 수치적 비교
        r'상위\s*\d+%', r'\d+위',
        # 교외 활동
        r'학원', r'과외', r'사교육',
    ]

    # 권장 동사 (학생부 기재에 적합)
    RECOMMENDED_VERBS = [
        "탐구함", "분석함", "이해함", "적용함", "발표함",
        "참여함", "협력함", "주도함", "기여함", "성장함",
        "발전함", "향상됨", "보임", "나타냄", "드러냄"
    ]

    @classmethod
    def validate_text(
        cls,
        text: str,
        section: NEISSection
    ) -> Dict[str, Any]:
        """
        NEIS 기재 텍스트 검증

        Args:
            text: 검증할 텍스트
            section: NEIS 영역

        Returns:
            검증 결과
        """
        issues = []
        warnings = []

        # 글자 수 확인
        char_count = len(text)
        limit = cls.CHAR_LIMITS[section]

        if char_count > limit.max_chars:
            issues.append(f"글자 수 초과: {char_count}/{limit.max_chars}자")
        elif char_count > limit.recommended_chars:
            warnings.append(f"권장 글자 수 초과: {char_count}/{limit.recommended_chars}자")

        # 금지 표현 확인
        for pattern in cls.PROHIBITED_EXPRESSIONS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                issues.append(f"금지 표현 발견: {matches}")

        # 문장 구조 확인
        if not text.endswith(('함.', '음.', '됨.', '임.')):
            warnings.append("학생부 기재 권장 어미 사용 권장 (~함, ~음, ~됨)")

        # 구체성 확인
        if len(text) < 100:
            warnings.append("내용이 너무 짧음. 구체적인 활동 내용 추가 권장")

        return {
            "valid": len(issues) == 0,
            "char_count": char_count,
            "max_chars": limit.max_chars,
            "issues": issues,
            "warnings": warnings,
            "section": section.value
        }

    @classmethod
    def format_research_record(
        cls,
        research_title: str,
        research_period: str,
        motivation: str,
        process: str,
        result: str,
        growth: str,
        max_chars: int = 500
    ) -> Dict[str, Any]:
        """
        자율연구 NEIS 기재문 생성

        Args:
            research_title: 연구 제목
            research_period: 연구 기간
            motivation: 연구 동기
            process: 연구 과정
            result: 연구 결과
            growth: 성장 및 배움
            max_chars: 최대 글자 수
        """
        # 기본 템플릿
        template = (
            f"'{research_title}' 주제로 {research_period} 동안 자율연구를 수행함. "
            f"{motivation} "
            f"{process} "
            f"{result} "
            f"이 과정에서 {growth}"
        )

        # 글자 수 조정
        if len(template) > max_chars:
            template = cls._compress_text(template, max_chars)

        # 검증
        validation = cls.validate_text(template, NEISSection.AUTONOMOUS_RESEARCH)

        return {
            "success": True,
            "text": template,
            "char_count": len(template),
            "validation": validation
        }

    @classmethod
    def format_club_activity(
        cls,
        club_name: str,
        role: str,
        activities: List[str],
        achievements: str,
        max_chars: int = 500
    ) -> Dict[str, Any]:
        """
        동아리활동 NEIS 기재문 생성
        """
        activity_text = ", ".join(activities[:3])  # 최대 3개 활동
        template = (
            f"({club_name}){role}(으)로 활동함. "
            f"{activity_text} 등의 활동에 참여함. "
            f"{achievements}"
        )

        if len(template) > max_chars:
            template = cls._compress_text(template, max_chars)

        validation = cls.validate_text(template, NEISSection.CLUB_ACTIVITY)

        return {
            "success": True,
            "text": template,
            "char_count": len(template),
            "validation": validation
        }

    @classmethod
    def format_subject_achievement(
        cls,
        subject: str,
        understanding: str,
        activities: List[str],
        growth: str,
        max_chars: int = 500
    ) -> Dict[str, Any]:
        """
        교과세부능력특기사항 NEIS 기재문 생성
        """
        activity_text = " ".join(activities[:2])
        template = (
            f"{subject} 교과에서 {understanding} "
            f"{activity_text} "
            f"{growth}"
        )

        if len(template) > max_chars:
            template = cls._compress_text(template, max_chars)

        validation = cls.validate_text(template, NEISSection.SUBJECT_ACHIEVEMENT)

        return {
            "success": True,
            "text": template,
            "char_count": len(template),
            "validation": validation
        }

    @classmethod
    def suggest_improvement(cls, text: str, section: NEISSection) -> Dict[str, Any]:
        """
        기재문 개선 제안

        Args:
            text: 원본 텍스트
            section: NEIS 영역
        """
        suggestions = []

        # 1. 구체성 체크
        vague_words = ['열심히', '잘', '많이', '매우', '정말']
        for word in vague_words:
            if word in text:
                suggestions.append(f"'{word}' 대신 구체적인 표현 사용 권장")

        # 2. 주어 생략 확인
        if not any(text.startswith(s) for s in ['학생', '본인', '해당']):
            suggestions.append("주어가 생략된 문장이 학생부 기재에 적합함")

        # 3. 수동태 권장
        active_patterns = [r'했다', r'했습니다', r'하였다']
        for pattern in active_patterns:
            if re.search(pattern, text):
                suggestions.append(f"'{pattern}' → '~함', '~하였음' 형태로 변경 권장")

        # 4. 객관적 표현 권장
        subjective = ['훌륭한', '뛰어난', '탁월한', '놀라운']
        for word in subjective:
            if word in text:
                suggestions.append(f"'{word}'은 주관적 표현. 객관적 사실 기반 서술 권장")

        return {
            "original": text,
            "section": section.value,
            "suggestions": suggestions,
            "recommendation_count": len(suggestions)
        }

    @classmethod
    def batch_validate(cls, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        다수 기재문 일괄 검증

        Args:
            records: [{"text": "", "section": NEISSection, "student_id": ""}]
        """
        results = []
        issues_count = 0
        warnings_count = 0

        for record in records:
            validation = cls.validate_text(
                record["text"],
                record["section"]
            )
            result = {
                "student_id": record.get("student_id", ""),
                "section": record["section"].value,
                "validation": validation
            }
            results.append(result)

            if not validation["valid"]:
                issues_count += 1
            if validation["warnings"]:
                warnings_count += 1

        return {
            "total": len(records),
            "issues": issues_count,
            "warnings": warnings_count,
            "passed": len(records) - issues_count,
            "results": results
        }

    @staticmethod
    def _compress_text(text: str, max_chars: int) -> str:
        """텍스트 압축"""
        if len(text) <= max_chars:
            return text

        # 문장 단위로 분리
        sentences = text.split('. ')
        result = []
        current_length = 0

        for sentence in sentences:
            if current_length + len(sentence) + 2 <= max_chars:
                result.append(sentence)
                current_length += len(sentence) + 2
            else:
                break

        compressed = '. '.join(result)
        if not compressed.endswith('.'):
            compressed += '.'

        return compressed


# 편의 함수들
def validate_research_record(text: str) -> Dict[str, Any]:
    """자율연구 기재문 검증"""
    return NEISHelper.validate_text(text, NEISSection.AUTONOMOUS_RESEARCH)


def create_research_record(
    title: str,
    motivation: str,
    process: str,
    result: str
) -> Dict[str, Any]:
    """자율연구 기재문 생성"""
    return NEISHelper.format_research_record(
        research_title=title,
        research_period="1학기",
        motivation=motivation,
        process=process,
        result=result,
        growth="과학적 탐구 능력과 문제 해결력이 향상됨."
    )


def get_char_limit(section_name: str) -> int:
    """영역별 글자 수 제한 조회"""
    section_map = {
        "자율연구": NEISSection.AUTONOMOUS_RESEARCH,
        "동아리": NEISSection.CLUB_ACTIVITY,
        "진로": NEISSection.CAREER,
        "교과": NEISSection.SUBJECT_ACHIEVEMENT,
        "행동특성": NEISSection.BEHAVIOR,
    }
    section = section_map.get(section_name, NEISSection.AUTONOMOUS_RESEARCH)
    return NEISHelper.CHAR_LIMITS[section].max_chars
