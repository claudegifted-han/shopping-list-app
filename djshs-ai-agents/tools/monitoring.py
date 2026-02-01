#!/usr/bin/env python3
"""
DJSHS AI Agent System - 모니터링 및 로깅 시스템
에이전트 사용 현황 추적 및 성능 모니터링

Usage:
    from monitoring import AgentMonitor, log_agent_call

    # 에이전트 호출 로깅
    log_agent_call("academic_affairs", "공문작성", success=True, duration=5.2)

    # 모니터링 대시보드
    monitor = AgentMonitor()
    monitor.print_dashboard()
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict
import sqlite3


# 로깅 설정
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "agent_system.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("dshs_agent_monitor")


@dataclass
class AgentCallLog:
    """에이전트 호출 로그"""
    timestamp: str
    agent_name: str
    task_type: str
    user_id: Optional[str]
    success: bool
    duration_seconds: float
    input_tokens: int
    output_tokens: int
    error_message: Optional[str]


class AgentMonitor:
    """에이전트 모니터링 클래스"""

    DB_FILE = LOG_DIR / "agent_metrics.db"

    def __init__(self):
        self._init_database()

    def _init_database(self):
        """SQLite 데이터베이스 초기화"""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                user_id TEXT,
                success INTEGER NOT NULL,
                duration_seconds REAL NOT NULL,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                error_message TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date TEXT PRIMARY KEY,
                total_calls INTEGER DEFAULT 0,
                success_calls INTEGER DEFAULT 0,
                total_duration REAL DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON agent_calls(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_name ON agent_calls(agent_name)
        """)

        conn.commit()
        conn.close()

    def log_call(
        self,
        agent_name: str,
        task_type: str,
        success: bool,
        duration_seconds: float,
        user_id: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error_message: Optional[str] = None
    ) -> None:
        """에이전트 호출 로깅"""
        timestamp = datetime.now().isoformat()

        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO agent_calls
            (timestamp, agent_name, task_type, user_id, success, duration_seconds,
             input_tokens, output_tokens, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, agent_name, task_type, user_id,
            1 if success else 0, duration_seconds,
            input_tokens, output_tokens, error_message
        ))

        # 일일 통계 업데이트
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO daily_stats (date, total_calls, success_calls, total_duration, total_tokens, unique_users)
            VALUES (?, 1, ?, ?, ?, 1)
            ON CONFLICT(date) DO UPDATE SET
                total_calls = total_calls + 1,
                success_calls = success_calls + ?,
                total_duration = total_duration + ?,
                total_tokens = total_tokens + ?
        """, (
            today, 1 if success else 0, duration_seconds, input_tokens + output_tokens,
            1 if success else 0, duration_seconds, input_tokens + output_tokens
        ))

        conn.commit()
        conn.close()

        # 콘솔 로깅
        status = "✅" if success else "❌"
        logger.info(f"{status} {agent_name} | {task_type} | {duration_seconds:.2f}s")

    def get_agent_stats(self, days: int = 7) -> Dict[str, Any]:
        """에이전트별 통계 조회"""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT
                agent_name,
                COUNT(*) as total_calls,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_calls,
                AVG(duration_seconds) as avg_duration,
                SUM(input_tokens + output_tokens) as total_tokens
            FROM agent_calls
            WHERE timestamp >= ?
            GROUP BY agent_name
            ORDER BY total_calls DESC
        """, (since,))

        rows = cursor.fetchall()
        conn.close()

        stats = {}
        for row in rows:
            agent_name, total, success, avg_dur, tokens = row
            stats[agent_name] = {
                "total_calls": total,
                "success_calls": success,
                "success_rate": round(success / total * 100, 1) if total > 0 else 0,
                "avg_duration": round(avg_dur, 2),
                "total_tokens": tokens or 0
            }

        return stats

    def get_task_type_stats(self, days: int = 7) -> Dict[str, int]:
        """작업 유형별 통계"""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT task_type, COUNT(*) as count
            FROM agent_calls
            WHERE timestamp >= ?
            GROUP BY task_type
            ORDER BY count DESC
            LIMIT 10
        """, (since,))

        rows = cursor.fetchall()
        conn.close()

        return {row[0]: row[1] for row in rows}

    def get_daily_trend(self, days: int = 14) -> List[Dict[str, Any]]:
        """일별 사용 추이"""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT date, total_calls, success_calls, total_duration, total_tokens
            FROM daily_stats
            ORDER BY date DESC
            LIMIT ?
        """, (days,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "date": row[0],
                "total_calls": row[1],
                "success_calls": row[2],
                "success_rate": round(row[2] / row[1] * 100, 1) if row[1] > 0 else 0,
                "total_duration": round(row[3], 1),
                "total_tokens": row[4]
            }
            for row in reversed(rows)
        ]

    def get_error_summary(self, days: int = 7) -> List[Dict[str, Any]]:
        """오류 요약"""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT agent_name, task_type, error_message, COUNT(*) as count
            FROM agent_calls
            WHERE timestamp >= ? AND success = 0 AND error_message IS NOT NULL
            GROUP BY agent_name, task_type, error_message
            ORDER BY count DESC
            LIMIT 20
        """, (since,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "agent": row[0],
                "task": row[1],
                "error": row[2],
                "count": row[3]
            }
            for row in rows
        ]

    def print_dashboard(self, days: int = 7) -> None:
        """대시보드 출력"""
        print("\n" + "="*70)
        print("📊 DJSHS AI Agent System - 모니터링 대시보드")
        print(f"   기간: 최근 {days}일 | 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*70)

        # 에이전트별 통계
        agent_stats = self.get_agent_stats(days)
        if agent_stats:
            print("\n🤖 에이전트별 통계")
            print("-"*70)
            print(f"{'에이전트':<20} {'호출':<8} {'성공률':<10} {'평균시간':<10} {'토큰':<10}")
            print("-"*70)
            for agent, stats in agent_stats.items():
                print(f"{agent:<20} {stats['total_calls']:<8} {stats['success_rate']:.1f}%{'':<5} {stats['avg_duration']:.2f}s{'':<5} {stats['total_tokens']:,}")
        else:
            print("\n⚠️ 아직 기록된 데이터가 없습니다.")

        # 작업 유형별 통계
        task_stats = self.get_task_type_stats(days)
        if task_stats:
            print("\n📋 인기 작업 유형 (Top 10)")
            print("-"*70)
            for task, count in task_stats.items():
                bar = "█" * min(count, 40)
                print(f"  {task:<25} {bar} {count}")

        # 일별 추이
        daily_trend = self.get_daily_trend(14)
        if daily_trend:
            print("\n📈 일별 사용 추이")
            print("-"*70)
            for day in daily_trend[-7:]:
                bar = "█" * min(day["total_calls"], 30)
                print(f"  {day['date']}: {bar} {day['total_calls']} ({day['success_rate']:.0f}%)")

        # 오류 요약
        errors = self.get_error_summary(days)
        if errors:
            print("\n❌ 최근 오류 (Top 5)")
            print("-"*70)
            for err in errors[:5]:
                print(f"  [{err['agent']}] {err['task']}: {err['error']} ({err['count']}건)")

        print("\n" + "="*70)

    def export_report(self, output_path: str = None, days: int = 7) -> str:
        """모니터링 리포트 JSON 내보내기"""
        if output_path is None:
            output_path = LOG_DIR / f"report_{datetime.now().strftime('%Y%m%d')}.json"

        report = {
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "agent_stats": self.get_agent_stats(days),
            "task_type_stats": self.get_task_type_stats(days),
            "daily_trend": self.get_daily_trend(days),
            "errors": self.get_error_summary(days)
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return str(output_path)


# 글로벌 모니터 인스턴스
_monitor = None


def get_monitor() -> AgentMonitor:
    """글로벌 모니터 인스턴스 반환"""
    global _monitor
    if _monitor is None:
        _monitor = AgentMonitor()
    return _monitor


def log_agent_call(
    agent_name: str,
    task_type: str,
    success: bool = True,
    duration: float = 0.0,
    **kwargs
) -> None:
    """에이전트 호출 로깅 (편의 함수)"""
    monitor = get_monitor()
    monitor.log_call(
        agent_name=agent_name,
        task_type=task_type,
        success=success,
        duration_seconds=duration,
        **kwargs
    )


class AgentCallContext:
    """에이전트 호출 컨텍스트 매니저"""

    def __init__(self, agent_name: str, task_type: str, user_id: str = None):
        self.agent_name = agent_name
        self.task_type = task_type
        self.user_id = user_id
        self.start_time = None
        self.success = True
        self.error_message = None

    def __enter__(self):
        self.start_time = datetime.now()
        logger.info(f"🚀 시작 | {self.agent_name} | {self.task_type}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val)

        log_agent_call(
            agent_name=self.agent_name,
            task_type=self.task_type,
            success=self.success,
            duration=duration,
            user_id=self.user_id,
            error_message=self.error_message
        )

        return False  # 예외 전파


def agent_call(agent_name: str, task_type: str):
    """에이전트 호출 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with AgentCallContext(agent_name, task_type):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# CLI 인터페이스
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DJSHS AI Agent 모니터링")
    parser.add_argument("--dashboard", "-d", action="store_true", help="대시보드 출력")
    parser.add_argument("--days", "-n", type=int, default=7, help="기간 (일)")
    parser.add_argument("--export", "-e", help="JSON 리포트 내보내기")
    parser.add_argument("--test", "-t", action="store_true", help="테스트 데이터 생성")

    args = parser.parse_args()

    monitor = AgentMonitor()

    if args.test:
        # 테스트 데이터 생성
        import random
        agents = ["academic_affairs", "curriculum", "evaluation", "gifted_edu", "ceo_strategy"]
        tasks = ["공문작성", "회의록정리", "일정조회", "성적분석", "연구현황"]

        for _ in range(50):
            agent = random.choice(agents)
            task = random.choice(tasks)
            success = random.random() > 0.1
            duration = random.uniform(1, 30)

            monitor.log_call(
                agent_name=agent,
                task_type=task,
                success=success,
                duration_seconds=duration,
                input_tokens=random.randint(100, 1000),
                output_tokens=random.randint(200, 2000)
            )

        print("✅ 테스트 데이터 50건 생성됨")

    if args.dashboard:
        monitor.print_dashboard(args.days)

    if args.export:
        path = monitor.export_report(args.export, args.days)
        print(f"✅ 리포트 저장: {path}")
