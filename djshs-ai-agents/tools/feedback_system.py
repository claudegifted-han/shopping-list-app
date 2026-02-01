#!/usr/bin/env python3
"""
DJSHS AI Agent System - 피드백 수집 시스템
사용자 만족도 수집 및 프롬프트 개선 제안

Usage:
    from feedback_system import FeedbackCollector, collect_feedback

    # 피드백 수집
    collect_feedback("academic_affairs", "공문작성", rating=5, comment="잘 작동함")

    # 분석 리포트
    collector = FeedbackCollector()
    collector.print_analysis()
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

# 데이터 저장 경로
DATA_DIR = Path(__file__).parent.parent / "logs"
DATA_DIR.mkdir(exist_ok=True)


@dataclass
class Feedback:
    """피드백 데이터"""
    timestamp: str
    agent_name: str
    task_type: str
    rating: int  # 1-5
    comment: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    response_time: Optional[float]
    was_helpful: bool
    improvement_suggestion: Optional[str]


class FeedbackCollector:
    """피드백 수집 및 분석"""

    DB_FILE = DATA_DIR / "feedback.db"

    # 에이전트 한글명
    AGENT_NAMES = {
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
        "brainstorm": "브레인스토밍",
    }

    def __init__(self):
        self._init_database()

    def _init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                user_id TEXT,
                session_id TEXT,
                response_time REAL,
                was_helpful INTEGER,
                improvement_suggestion TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompt_improvements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                current_behavior TEXT,
                suggested_improvement TEXT,
                priority TEXT,
                status TEXT DEFAULT 'pending',
                implemented_at TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_agent ON feedback(agent_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp)
        """)

        conn.commit()
        conn.close()

    def collect(
        self,
        agent_name: str,
        task_type: str,
        rating: int,
        comment: str = None,
        user_id: str = None,
        session_id: str = None,
        response_time: float = None,
        was_helpful: bool = True,
        improvement_suggestion: str = None
    ) -> int:
        """피드백 수집"""
        if not 1 <= rating <= 5:
            raise ValueError("rating은 1-5 사이여야 합니다")

        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO feedback
            (timestamp, agent_name, task_type, rating, comment, user_id,
             session_id, response_time, was_helpful, improvement_suggestion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            agent_name,
            task_type,
            rating,
            comment,
            user_id,
            session_id,
            response_time,
            1 if was_helpful else 0,
            improvement_suggestion
        ))

        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # 낮은 평점이면 개선 제안 자동 생성
        if rating <= 2:
            self._auto_suggest_improvement(agent_name, task_type, rating, comment)

        return feedback_id

    def _auto_suggest_improvement(
        self,
        agent_name: str,
        task_type: str,
        rating: int,
        comment: str = None
    ):
        """낮은 평점에 대한 자동 개선 제안"""
        issue_types = {
            1: "critical",
            2: "major"
        }

        suggestion = self._generate_improvement_suggestion(agent_name, task_type, comment)

        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO prompt_improvements
            (created_at, agent_name, issue_type, current_behavior,
             suggested_improvement, priority, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """, (
            datetime.now().isoformat(),
            agent_name,
            issue_types.get(rating, "minor"),
            comment or f"{task_type} 작업 시 불만족",
            suggestion,
            "high" if rating == 1 else "medium"
        ))

        conn.commit()
        conn.close()

    def _generate_improvement_suggestion(
        self,
        agent_name: str,
        task_type: str,
        comment: str = None
    ) -> str:
        """개선 제안 생성"""
        suggestions = {
            "공문작성": "공문 템플릿 형식 검토 및 필수 항목 체크리스트 추가",
            "회의록정리": "회의록 구조화 템플릿 개선 및 핵심 의결사항 강조",
            "성적분석": "분석 결과 시각화 및 해석 가이드 추가",
            "일정조회": "일정 필터링 옵션 다양화 및 응답 형식 개선",
            "연구현황": "연구 상태별 분류 명확화 및 요약 정보 추가",
        }

        base_suggestion = suggestions.get(task_type, f"{task_type} 작업 프롬프트 전반 검토 필요")

        if comment:
            return f"{base_suggestion}\n\n사용자 피드백: {comment}"

        return base_suggestion

    # ==========================================
    # 분석 기능
    # ==========================================

    def get_summary_stats(self, days: int = 30) -> Dict[str, Any]:
        """요약 통계"""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        # 전체 통계
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                AVG(rating) as avg_rating,
                SUM(CASE WHEN was_helpful = 1 THEN 1 ELSE 0 END) as helpful_count
            FROM feedback
            WHERE timestamp >= ?
        """, (since,))

        row = cursor.fetchone()
        total, avg_rating, helpful = row

        # NPS 계산 (9-10: 추천, 7-8: 중립, 1-6: 비추천 → 5점 척도 변환)
        cursor.execute("""
            SELECT
                SUM(CASE WHEN rating >= 5 THEN 1 ELSE 0 END) as promoters,
                SUM(CASE WHEN rating >= 3 AND rating < 5 THEN 1 ELSE 0 END) as passives,
                SUM(CASE WHEN rating < 3 THEN 1 ELSE 0 END) as detractors
            FROM feedback
            WHERE timestamp >= ?
        """, (since,))

        promoters, passives, detractors = cursor.fetchone()
        nps = 0
        if total and total > 0:
            nps = ((promoters or 0) - (detractors or 0)) / total * 100

        conn.close()

        return {
            "period_days": days,
            "total_feedback": total or 0,
            "avg_rating": round(avg_rating or 0, 2),
            "helpful_rate": round((helpful or 0) / total * 100, 1) if total else 0,
            "nps_score": round(nps, 1),
            "promoters": promoters or 0,
            "detractors": detractors or 0
        }

    def get_agent_ratings(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """에이전트별 평점"""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT
                agent_name,
                COUNT(*) as count,
                AVG(rating) as avg_rating,
                MIN(rating) as min_rating,
                MAX(rating) as max_rating
            FROM feedback
            WHERE timestamp >= ?
            GROUP BY agent_name
            ORDER BY avg_rating DESC
        """, (since,))

        results = {}
        for row in cursor.fetchall():
            agent, count, avg, min_r, max_r = row
            results[agent] = {
                "name_ko": self.AGENT_NAMES.get(agent, agent),
                "count": count,
                "avg_rating": round(avg, 2),
                "min_rating": min_r,
                "max_rating": max_r,
                "status": "good" if avg >= 4 else ("warning" if avg >= 3 else "critical")
            }

        conn.close()
        return results

    def get_task_ratings(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """작업 유형별 평점"""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT
                task_type,
                COUNT(*) as count,
                AVG(rating) as avg_rating
            FROM feedback
            WHERE timestamp >= ?
            GROUP BY task_type
            ORDER BY count DESC
        """, (since,))

        results = {}
        for row in cursor.fetchall():
            task, count, avg = row
            results[task] = {
                "count": count,
                "avg_rating": round(avg, 2),
                "status": "good" if avg >= 4 else ("warning" if avg >= 3 else "critical")
            }

        conn.close()
        return results

    def get_pending_improvements(self) -> List[Dict[str, Any]]:
        """대기 중인 개선 사항"""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id, created_at, agent_name, issue_type,
                current_behavior, suggested_improvement, priority
            FROM prompt_improvements
            WHERE status = 'pending'
            ORDER BY
                CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                created_at DESC
        """)

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "created_at": row[1],
                "agent": row[2],
                "agent_ko": self.AGENT_NAMES.get(row[2], row[2]),
                "issue_type": row[3],
                "current_behavior": row[4],
                "suggestion": row[5],
                "priority": row[6]
            })

        conn.close()
        return results

    def get_recent_comments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 코멘트"""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, agent_name, task_type, rating, comment
            FROM feedback
            WHERE comment IS NOT NULL AND comment != ''
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "timestamp": row[0],
                "agent": row[1],
                "agent_ko": self.AGENT_NAMES.get(row[1], row[1]),
                "task": row[2],
                "rating": row[3],
                "comment": row[4]
            })

        conn.close()
        return results

    def mark_improvement_done(self, improvement_id: int) -> bool:
        """개선 사항 완료 처리"""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE prompt_improvements
            SET status = 'implemented', implemented_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), improvement_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    # ==========================================
    # 출력 기능
    # ==========================================

    def print_analysis(self, days: int = 30):
        """분석 리포트 출력"""
        print("\n" + "="*70)
        print("📊 DJSHS AI Agent System - 피드백 분석 리포트")
        print(f"   기간: 최근 {days}일 | 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*70)

        # 요약 통계
        stats = self.get_summary_stats(days)
        print(f"\n📈 요약 통계")
        print("-"*70)
        print(f"   총 피드백: {stats['total_feedback']}건")
        print(f"   평균 평점: {'⭐' * round(stats['avg_rating'])} {stats['avg_rating']}/5.0")
        print(f"   도움됨 비율: {stats['helpful_rate']}%")
        print(f"   NPS 점수: {stats['nps_score']} (추천 {stats['promoters']}, 비추천 {stats['detractors']})")

        # 에이전트별 평점
        agent_ratings = self.get_agent_ratings(days)
        if agent_ratings:
            print(f"\n🤖 에이전트별 평점")
            print("-"*70)
            print(f"{'에이전트':<15} {'평점':<10} {'건수':<8} {'상태':<10}")
            print("-"*70)
            for agent, data in agent_ratings.items():
                status_icon = {"good": "✅", "warning": "⚠️", "critical": "❌"}[data['status']]
                stars = "⭐" * round(data['avg_rating'])
                print(f"{data['name_ko']:<15} {stars:<10} {data['count']:<8} {status_icon}")

        # 작업 유형별 평점
        task_ratings = self.get_task_ratings(days)
        if task_ratings:
            print(f"\n📋 작업 유형별 평점")
            print("-"*70)
            for task, data in task_ratings.items():
                status_icon = {"good": "✅", "warning": "⚠️", "critical": "❌"}[data['status']]
                print(f"   {task}: {'⭐' * round(data['avg_rating'])} ({data['count']}건) {status_icon}")

        # 대기 중인 개선 사항
        improvements = self.get_pending_improvements()
        if improvements:
            print(f"\n🔧 대기 중인 개선 사항 ({len(improvements)}건)")
            print("-"*70)
            for imp in improvements[:5]:
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[imp['priority']]
                print(f"   {priority_icon} [{imp['agent_ko']}] {imp['suggestion'][:50]}...")

        # 최근 코멘트
        comments = self.get_recent_comments(5)
        if comments:
            print(f"\n💬 최근 피드백 코멘트")
            print("-"*70)
            for c in comments:
                stars = "⭐" * c['rating']
                print(f"   [{c['agent_ko']}] {stars}")
                print(f"      \"{c['comment'][:60]}...\"" if len(c['comment']) > 60 else f"      \"{c['comment']}\"")

        print("\n" + "="*70)

    def export_report(self, output_path: str = None, days: int = 30) -> str:
        """JSON 리포트 내보내기"""
        if output_path is None:
            output_path = DATA_DIR / f"feedback_report_{datetime.now().strftime('%Y%m%d')}.json"

        report = {
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "summary": self.get_summary_stats(days),
            "agent_ratings": self.get_agent_ratings(days),
            "task_ratings": self.get_task_ratings(days),
            "pending_improvements": self.get_pending_improvements(),
            "recent_comments": self.get_recent_comments(20)
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return str(output_path)


# 편의 함수
_collector = None


def get_collector() -> FeedbackCollector:
    """글로벌 컬렉터 인스턴스"""
    global _collector
    if _collector is None:
        _collector = FeedbackCollector()
    return _collector


def collect_feedback(
    agent_name: str,
    task_type: str,
    rating: int,
    comment: str = None,
    **kwargs
) -> int:
    """피드백 수집 편의 함수"""
    return get_collector().collect(
        agent_name=agent_name,
        task_type=task_type,
        rating=rating,
        comment=comment,
        **kwargs
    )


# CLI 인터페이스
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DJSHS AI Agent 피드백 시스템")
    parser.add_argument("--analysis", "-a", action="store_true", help="분석 리포트 출력")
    parser.add_argument("--days", "-d", type=int, default=30, help="분석 기간 (일)")
    parser.add_argument("--export", "-e", help="JSON 리포트 내보내기")
    parser.add_argument("--test", "-t", action="store_true", help="테스트 데이터 생성")
    parser.add_argument("--improvements", "-i", action="store_true", help="개선 사항 목록")

    args = parser.parse_args()

    collector = FeedbackCollector()

    if args.test:
        # 테스트 데이터 생성
        import random

        agents = ["academic_affairs", "curriculum", "evaluation", "gifted_edu", "ceo_strategy"]
        tasks = ["공문작성", "회의록정리", "성적분석", "일정조회", "연구현황"]
        comments = [
            "잘 작동합니다",
            "응답이 정확해요",
            "형식이 조금 아쉬워요",
            "더 빠르면 좋겠어요",
            "매우 유용합니다",
            None, None, None
        ]

        for _ in range(30):
            agent = random.choice(agents)
            task = random.choice(tasks)
            rating = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 15, 35, 35])[0]
            comment = random.choice(comments)

            collector.collect(
                agent_name=agent,
                task_type=task,
                rating=rating,
                comment=comment,
                was_helpful=rating >= 3
            )

        print("✅ 테스트 피드백 30건 생성됨")

    if args.analysis:
        collector.print_analysis(args.days)

    if args.export:
        path = collector.export_report(args.export, args.days)
        print(f"✅ 리포트 저장: {path}")

    if args.improvements:
        improvements = collector.get_pending_improvements()
        print(f"\n🔧 대기 중인 개선 사항 ({len(improvements)}건)")
        print("-"*60)
        for imp in improvements:
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[imp['priority']]
            print(f"\n{priority_icon} ID: {imp['id']}")
            print(f"   에이전트: {imp['agent_ko']}")
            print(f"   문제: {imp['current_behavior']}")
            print(f"   제안: {imp['suggestion']}")
