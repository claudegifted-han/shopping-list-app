#!/usr/bin/env python3
"""
DSHS AI Agent System - 외부 시스템 연동
Google Calendar, 이메일, NEIS 등 외부 시스템 연동 도구

Usage:
    from external_integrations import CalendarManager, EmailNotifier

    # 캘린더 이벤트 생성
    calendar = CalendarManager()
    calendar.create_event("회의", "2026-02-15 10:00", "2026-02-15 11:00")

    # 이메일 알림
    email = EmailNotifier()
    email.send_notification("제목", "내용", ["recipient@school.kr"])
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod


# =============================================================================
# 캘린더 연동
# =============================================================================

@dataclass
class CalendarEvent:
    """캘린더 이벤트"""
    id: str
    title: str
    start: str
    end: str
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    reminder_minutes: int = 30
    category: str = "general"


class CalendarManager:
    """캘린더 관리자 (Google Calendar API 연동 준비)"""

    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path
        self.is_configured = self._check_configuration()
        self.local_events: List[CalendarEvent] = []  # 로컬 시뮬레이션용

    def _check_configuration(self) -> bool:
        """설정 확인"""
        # 실제 구현 시 Google OAuth 자격 증명 확인
        return os.environ.get("GOOGLE_CALENDAR_CREDENTIALS") is not None

    def create_event(
        self,
        title: str,
        start: str,
        end: str,
        description: str = None,
        location: str = None,
        attendees: List[str] = None,
        reminder_minutes: int = 30,
        category: str = "general"
    ) -> Dict[str, Any]:
        """이벤트 생성"""
        event = CalendarEvent(
            id=f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=title,
            start=start,
            end=end,
            description=description,
            location=location,
            attendees=attendees,
            reminder_minutes=reminder_minutes,
            category=category
        )

        if self.is_configured:
            # 실제 Google Calendar API 호출
            return self._create_google_event(event)
        else:
            # 로컬 시뮬레이션
            self.local_events.append(event)
            return {
                "success": True,
                "mode": "simulation",
                "event": asdict(event),
                "message": "이벤트가 로컬에 저장되었습니다. (Google Calendar 미연동)"
            }

    def _create_google_event(self, event: CalendarEvent) -> Dict[str, Any]:
        """Google Calendar에 이벤트 생성 (실제 구현 시)"""
        # TODO: Google Calendar API 연동
        # from googleapiclient.discovery import build
        # service = build('calendar', 'v3', credentials=self.credentials)
        # result = service.events().insert(calendarId='primary', body=event_body).execute()
        return {
            "success": True,
            "mode": "google_calendar",
            "event_id": event.id,
            "message": "Google Calendar API 연동 필요"
        }

    def get_upcoming_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """다가오는 이벤트 조회"""
        if self.is_configured:
            return self._get_google_events(days)
        else:
            # 로컬 이벤트 반환
            return [asdict(e) for e in self.local_events]

    def _get_google_events(self, days: int) -> List[Dict[str, Any]]:
        """Google Calendar에서 이벤트 조회"""
        # TODO: Google Calendar API 연동
        return []

    def sync_from_notion(self, notion_events: List[Dict]) -> Dict[str, Any]:
        """Notion 학사일정과 동기화"""
        synced = 0
        errors = []

        for event in notion_events:
            try:
                self.create_event(
                    title=event.get("일정명", event.get("title", "Untitled")),
                    start=event.get("시작일", event.get("start")),
                    end=event.get("종료일", event.get("end")),
                    category=event.get("유형", "general"),
                    location=event.get("장소")
                )
                synced += 1
            except Exception as e:
                errors.append({"event": event, "error": str(e)})

        return {
            "synced": synced,
            "errors": len(errors),
            "error_details": errors
        }


# =============================================================================
# 이메일 알림
# =============================================================================

@dataclass
class EmailTemplate:
    """이메일 템플릿"""
    id: str
    name: str
    subject_template: str
    body_template: str
    category: str


class EmailNotifier:
    """이메일 알림 관리자"""

    TEMPLATES = {
        "meeting_reminder": EmailTemplate(
            id="meeting_reminder",
            name="회의 알림",
            subject_template="[대전과학고] {meeting_name} 회의 알림",
            body_template="""
안녕하세요.

다음 회의가 예정되어 있습니다.

📌 회의명: {meeting_name}
📅 일시: {date_time}
📍 장소: {location}
📋 안건: {agenda}

참석을 부탁드립니다.

대전과학고등학교 {department}
            """,
            category="meeting"
        ),
        "event_notification": EmailTemplate(
            id="event_notification",
            name="행사 안내",
            subject_template="[대전과학고] {event_name} 안내",
            body_template="""
안녕하세요.

다음 행사를 안내드립니다.

📌 행사명: {event_name}
📅 일시: {date_time}
📍 장소: {location}
👥 대상: {target}

{description}

대전과학고등학교
            """,
            category="event"
        ),
        "document_notification": EmailTemplate(
            id="document_notification",
            name="문서 알림",
            subject_template="[대전과학고] {doc_title}",
            body_template="""
안녕하세요.

새로운 문서가 등록되었습니다.

📄 문서명: {doc_title}
📁 유형: {doc_type}
🏢 작성부서: {department}

문서를 확인해 주시기 바랍니다.

대전과학고등학교
            """,
            category="document"
        ),
        "research_update": EmailTemplate(
            id="research_update",
            name="연구 현황 알림",
            subject_template="[대전과학고] {research_title} 연구 현황 업데이트",
            body_template="""
안녕하세요.

자율연구 현황이 업데이트되었습니다.

🔬 연구제목: {research_title}
👨‍🎓 연구자: {researcher}
📊 상태: {status}
📝 변경사항: {changes}

지도교사 확인이 필요합니다.

대전과학고등학교 영재교육부
            """,
            category="research"
        )
    }

    def __init__(self, smtp_config: Dict = None):
        self.smtp_config = smtp_config or {}
        self.is_configured = self._check_configuration()
        self.sent_log: List[Dict] = []  # 발송 로그

    def _check_configuration(self) -> bool:
        """SMTP 설정 확인"""
        required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD"]
        return all(os.environ.get(key) for key in required)

    def send_notification(
        self,
        subject: str,
        body: str,
        recipients: List[str],
        cc: List[str] = None,
        attachments: List[str] = None
    ) -> Dict[str, Any]:
        """알림 발송"""
        notification = {
            "timestamp": datetime.now().isoformat(),
            "subject": subject,
            "body": body,
            "recipients": recipients,
            "cc": cc,
            "attachments": attachments
        }

        if self.is_configured:
            return self._send_email(notification)
        else:
            # 시뮬레이션 모드
            self.sent_log.append(notification)
            return {
                "success": True,
                "mode": "simulation",
                "message": f"이메일이 시뮬레이션되었습니다. (수신자: {len(recipients)}명)",
                "notification": notification
            }

    def _send_email(self, notification: Dict) -> Dict[str, Any]:
        """실제 이메일 발송 (SMTP)"""
        # TODO: SMTP 연동
        # import smtplib
        # from email.mime.text import MIMEText
        return {
            "success": True,
            "mode": "smtp",
            "message": "SMTP 연동 필요"
        }

    def send_from_template(
        self,
        template_id: str,
        recipients: List[str],
        variables: Dict[str, str]
    ) -> Dict[str, Any]:
        """템플릿 기반 발송"""
        template = self.TEMPLATES.get(template_id)
        if not template:
            return {"success": False, "error": f"템플릿 '{template_id}'을(를) 찾을 수 없습니다."}

        try:
            subject = template.subject_template.format(**variables)
            body = template.body_template.format(**variables)
            return self.send_notification(subject, body, recipients)
        except KeyError as e:
            return {"success": False, "error": f"템플릿 변수 누락: {e}"}

    def get_templates(self) -> List[Dict[str, str]]:
        """사용 가능한 템플릿 목록"""
        return [
            {"id": t.id, "name": t.name, "category": t.category}
            for t in self.TEMPLATES.values()
        ]


# =============================================================================
# NEIS 연동 (시뮬레이션)
# =============================================================================

class NEISConnector:
    """NEIS 연동 (시뮬레이션)"""

    def __init__(self):
        self.is_configured = os.environ.get("NEIS_API_KEY") is not None

    def get_student_info(self, student_id: str) -> Dict[str, Any]:
        """학생 정보 조회 (보안 제한)"""
        return {
            "success": False,
            "error": "NEIS 학생 정보는 보안상 AI 직접 접근이 제한됩니다.",
            "action": "교무운영부에 문의하세요."
        }

    def get_school_schedule(self, year: int, month: int) -> Dict[str, Any]:
        """학사일정 조회"""
        if not self.is_configured:
            return {
                "success": True,
                "mode": "simulation",
                "message": "NEIS API 연동 시 실제 학사일정 조회 가능",
                "data": []
            }

        # TODO: NEIS Open API 연동
        # https://open.neis.go.kr/portal/data/service/selectServicePage.do
        return {"success": True, "data": []}

    def get_meal_info(self, date: str) -> Dict[str, Any]:
        """급식 정보 조회"""
        # NEIS 급식 API는 공개 API로 연동 가능
        return {
            "success": True,
            "mode": "simulation",
            "message": "NEIS 급식 API 연동 가능",
            "data": {
                "date": date,
                "lunch": "시뮬레이션 급식 메뉴"
            }
        }


# =============================================================================
# 통합 외부 연동 관리자
# =============================================================================

class ExternalIntegrationManager:
    """외부 연동 통합 관리자"""

    def __init__(self):
        self.calendar = CalendarManager()
        self.email = EmailNotifier()
        self.neis = NEISConnector()

    def get_status(self) -> Dict[str, Any]:
        """연동 상태 확인"""
        return {
            "google_calendar": {
                "configured": self.calendar.is_configured,
                "status": "connected" if self.calendar.is_configured else "simulation"
            },
            "email_smtp": {
                "configured": self.email.is_configured,
                "status": "connected" if self.email.is_configured else "simulation"
            },
            "neis": {
                "configured": self.neis.is_configured,
                "status": "connected" if self.neis.is_configured else "simulation"
            }
        }

    def notify_meeting(
        self,
        meeting_name: str,
        date_time: str,
        location: str,
        agenda: str,
        attendees: List[str],
        department: str = "교무운영부"
    ) -> Dict[str, Any]:
        """회의 알림 (캘린더 + 이메일)"""
        results = {}

        # 캘린더 이벤트 생성
        end_time = (datetime.fromisoformat(date_time.replace(" ", "T")) + timedelta(hours=1)).isoformat()
        results["calendar"] = self.calendar.create_event(
            title=meeting_name,
            start=date_time.replace(" ", "T"),
            end=end_time,
            location=location,
            description=agenda,
            attendees=attendees,
            category="meeting"
        )

        # 이메일 알림
        results["email"] = self.email.send_from_template(
            "meeting_reminder",
            attendees,
            {
                "meeting_name": meeting_name,
                "date_time": date_time,
                "location": location,
                "agenda": agenda,
                "department": department
            }
        )

        return results

    def notify_event(
        self,
        event_name: str,
        date_time: str,
        location: str,
        target: str,
        description: str,
        notify_list: List[str]
    ) -> Dict[str, Any]:
        """행사 알림"""
        return self.email.send_from_template(
            "event_notification",
            notify_list,
            {
                "event_name": event_name,
                "date_time": date_time,
                "location": location,
                "target": target,
                "description": description
            }
        )


# CLI 인터페이스
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DSHS AI Agent 외부 연동")
    parser.add_argument("--status", "-s", action="store_true", help="연동 상태 확인")
    parser.add_argument("--test-calendar", action="store_true", help="캘린더 테스트")
    parser.add_argument("--test-email", action="store_true", help="이메일 테스트")
    parser.add_argument("--templates", action="store_true", help="이메일 템플릿 목록")

    args = parser.parse_args()

    manager = ExternalIntegrationManager()

    if args.status:
        print("\n📡 외부 시스템 연동 상태")
        print("="*50)
        status = manager.get_status()
        for system, info in status.items():
            icon = "✅" if info["configured"] else "⚠️"
            print(f"  {icon} {system}: {info['status']}")
        print("="*50)

    if args.test_calendar:
        print("\n📅 캘린더 테스트")
        result = manager.calendar.create_event(
            title="테스트 회의",
            start="2026-02-15T10:00:00",
            end="2026-02-15T11:00:00",
            location="회의실",
            description="테스트 이벤트입니다."
        )
        print(f"  결과: {result['message']}")

    if args.test_email:
        print("\n📧 이메일 테스트")
        result = manager.email.send_notification(
            subject="[테스트] DSHS AI Agent 이메일 테스트",
            body="이것은 테스트 이메일입니다.",
            recipients=["test@school.kr"]
        )
        print(f"  결과: {result['message']}")

    if args.templates:
        print("\n📋 이메일 템플릿 목록")
        print("="*50)
        for t in manager.email.get_templates():
            print(f"  • {t['id']}: {t['name']} ({t['category']})")
