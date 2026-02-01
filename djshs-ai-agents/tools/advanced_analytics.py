#!/usr/bin/env python3
"""
DJSHS AI Agent System - 고급 분석 및 예측
트렌드 분석, 예측 모델, 자동 인사이트 생성

Usage:
    from advanced_analytics import AnalyticsEngine

    engine = AnalyticsEngine()
    engine.generate_insights()
    engine.print_executive_report()
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math

# 데이터 디렉토리
DATA_DIR = Path(__file__).parent.parent / "logs"


@dataclass
class Insight:
    """분석 인사이트"""
    id: str
    category: str  # usage, performance, trend, anomaly, recommendation
    title: str
    description: str
    severity: str  # info, warning, critical
    metric_value: Optional[float] = None
    comparison_value: Optional[float] = None
    action_items: Optional[List[str]] = None


class AnalyticsEngine:
    """고급 분석 엔진"""

    METRICS_DB = DATA_DIR / "agent_metrics.db"
    FEEDBACK_DB = DATA_DIR / "feedback.db"

    def __init__(self):
        self.insights: List[Insight] = []

    # ==========================================================================
    # 데이터 수집
    # ==========================================================================

    def _get_usage_data(self, days: int = 30) -> List[Dict]:
        """사용량 데이터 조회"""
        if not self.METRICS_DB.exists():
            return []

        conn = sqlite3.connect(self.METRICS_DB)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT
                DATE(timestamp) as date,
                agent_name,
                task_type,
                COUNT(*) as calls,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success,
                AVG(duration_seconds) as avg_duration,
                SUM(input_tokens + output_tokens) as tokens
            FROM agent_calls
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp), agent_name, task_type
            ORDER BY date
        """, (since,))

        columns = ["date", "agent", "task", "calls", "success", "avg_duration", "tokens"]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def _get_feedback_data(self, days: int = 30) -> List[Dict]:
        """피드백 데이터 조회"""
        if not self.FEEDBACK_DB.exists():
            return []

        conn = sqlite3.connect(self.FEEDBACK_DB)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT
                DATE(timestamp) as date,
                agent_name,
                task_type,
                AVG(rating) as avg_rating,
                COUNT(*) as count
            FROM feedback
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp), agent_name, task_type
            ORDER BY date
        """, (since,))

        columns = ["date", "agent", "task", "avg_rating", "count"]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    # ==========================================================================
    # 트렌드 분석
    # ==========================================================================

    def analyze_usage_trend(self, days: int = 30) -> Dict[str, Any]:
        """사용량 트렌드 분석"""
        data = self._get_usage_data(days)
        if not data:
            return {"trend": "no_data", "insights": []}

        # 일별 집계
        daily = defaultdict(lambda: {"calls": 0, "success": 0, "tokens": 0})
        for row in data:
            daily[row["date"]]["calls"] += row["calls"]
            daily[row["date"]]["success"] += row["success"]
            daily[row["date"]]["tokens"] += row["tokens"] or 0

        dates = sorted(daily.keys())
        if len(dates) < 7:
            return {"trend": "insufficient_data", "insights": []}

        # 최근 7일 vs 이전 7일 비교
        recent = dates[-7:]
        earlier = dates[-14:-7] if len(dates) >= 14 else dates[:7]

        recent_avg = sum(daily[d]["calls"] for d in recent) / len(recent)
        earlier_avg = sum(daily[d]["calls"] for d in earlier) / len(earlier) if earlier else recent_avg

        change_pct = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0

        trend = "increasing" if change_pct > 10 else ("decreasing" if change_pct < -10 else "stable")

        # 인사이트 생성
        insights = []
        if trend == "increasing":
            insights.append(Insight(
                id="TREND001",
                category="trend",
                title="사용량 증가 추세",
                description=f"최근 7일 사용량이 이전 대비 {change_pct:.1f}% 증가했습니다.",
                severity="info",
                metric_value=recent_avg,
                comparison_value=earlier_avg,
                action_items=["시스템 용량 모니터링 강화", "사용자 만족도 조사 실시"]
            ))
        elif trend == "decreasing":
            insights.append(Insight(
                id="TREND002",
                category="trend",
                title="사용량 감소 추세",
                description=f"최근 7일 사용량이 이전 대비 {abs(change_pct):.1f}% 감소했습니다.",
                severity="warning",
                metric_value=recent_avg,
                comparison_value=earlier_avg,
                action_items=["사용자 피드백 수집", "기능 홍보 강화", "사용성 개선 검토"]
            ))

        self.insights.extend(insights)

        return {
            "trend": trend,
            "change_percent": round(change_pct, 1),
            "recent_avg_daily": round(recent_avg, 1),
            "earlier_avg_daily": round(earlier_avg, 1),
            "insights": [i.title for i in insights]
        }

    def analyze_performance(self, days: int = 30) -> Dict[str, Any]:
        """성능 분석"""
        data = self._get_usage_data(days)
        if not data:
            return {"status": "no_data"}

        # 에이전트별 성공률
        agent_stats = defaultdict(lambda: {"calls": 0, "success": 0, "duration": []})
        for row in data:
            agent_stats[row["agent"]]["calls"] += row["calls"]
            agent_stats[row["agent"]]["success"] += row["success"]
            if row["avg_duration"]:
                agent_stats[row["agent"]]["duration"].append(row["avg_duration"])

        # 문제 에이전트 식별
        problem_agents = []
        slow_agents = []

        for agent, stats in agent_stats.items():
            success_rate = stats["success"] / stats["calls"] * 100 if stats["calls"] > 0 else 0
            avg_duration = sum(stats["duration"]) / len(stats["duration"]) if stats["duration"] else 0

            if success_rate < 85 and stats["calls"] >= 5:
                problem_agents.append({
                    "agent": agent,
                    "success_rate": round(success_rate, 1),
                    "calls": stats["calls"]
                })
                self.insights.append(Insight(
                    id=f"PERF_{agent}",
                    category="performance",
                    title=f"{agent} 성공률 저하",
                    description=f"성공률 {success_rate:.1f}%로 목표(85%) 미달",
                    severity="warning" if success_rate >= 70 else "critical",
                    metric_value=success_rate,
                    action_items=["프롬프트 튜닝 검토", "오류 로그 분석", "테스트 케이스 추가"]
                ))

            if avg_duration > 20:
                slow_agents.append({
                    "agent": agent,
                    "avg_duration": round(avg_duration, 1)
                })

        return {
            "total_agents": len(agent_stats),
            "problem_agents": problem_agents,
            "slow_agents": slow_agents
        }

    def analyze_satisfaction(self, days: int = 30) -> Dict[str, Any]:
        """만족도 분석"""
        data = self._get_feedback_data(days)
        if not data:
            return {"status": "no_data"}

        # 전체 평균
        total_ratings = sum(d["avg_rating"] * d["count"] for d in data)
        total_count = sum(d["count"] for d in data)
        overall_avg = total_ratings / total_count if total_count > 0 else 0

        # 에이전트별 분석
        agent_ratings = defaultdict(lambda: {"total": 0, "count": 0})
        for row in data:
            agent_ratings[row["agent"]]["total"] += row["avg_rating"] * row["count"]
            agent_ratings[row["agent"]]["count"] += row["count"]

        low_satisfaction = []
        for agent, stats in agent_ratings.items():
            avg = stats["total"] / stats["count"] if stats["count"] > 0 else 0
            if avg < 3.5 and stats["count"] >= 3:
                low_satisfaction.append({
                    "agent": agent,
                    "avg_rating": round(avg, 2),
                    "count": stats["count"]
                })
                self.insights.append(Insight(
                    id=f"SAT_{agent}",
                    category="satisfaction",
                    title=f"{agent} 만족도 저하",
                    description=f"평균 평점 {avg:.1f}/5.0으로 개선 필요",
                    severity="warning",
                    metric_value=avg,
                    action_items=["사용자 피드백 상세 분석", "UX 개선", "응답 품질 향상"]
                ))

        return {
            "overall_avg": round(overall_avg, 2),
            "total_feedback": total_count,
            "low_satisfaction_agents": low_satisfaction
        }

    # ==========================================================================
    # 예측 분석
    # ==========================================================================

    def predict_usage(self, days_ahead: int = 7) -> Dict[str, Any]:
        """사용량 예측 (단순 이동평균 기반)"""
        data = self._get_usage_data(30)
        if len(data) < 14:
            return {"status": "insufficient_data"}

        # 일별 집계
        daily = defaultdict(int)
        for row in data:
            daily[row["date"]] += row["calls"]

        dates = sorted(daily.keys())
        values = [daily[d] for d in dates]

        # 7일 이동평균
        if len(values) >= 7:
            ma7 = sum(values[-7:]) / 7
        else:
            ma7 = sum(values) / len(values)

        # 트렌드 계산 (최근 14일 기울기)
        if len(values) >= 14:
            first_half = sum(values[-14:-7]) / 7
            second_half = sum(values[-7:]) / 7
            trend = (second_half - first_half) / 7
        else:
            trend = 0

        # 예측
        predictions = []
        current = ma7
        for i in range(days_ahead):
            predicted = max(0, current + trend * (i + 1))
            predictions.append({
                "day": i + 1,
                "predicted_calls": round(predicted, 1)
            })

        # 인사이트
        if trend > 1:
            self.insights.append(Insight(
                id="PRED001",
                category="prediction",
                title="사용량 증가 예측",
                description=f"향후 {days_ahead}일간 일평균 {ma7 + trend * days_ahead / 2:.0f}건 예상",
                severity="info",
                metric_value=ma7 + trend * days_ahead / 2
            ))

        return {
            "current_avg": round(ma7, 1),
            "trend_per_day": round(trend, 2),
            "predictions": predictions
        }

    def identify_anomalies(self, days: int = 30) -> List[Dict[str, Any]]:
        """이상 징후 탐지"""
        data = self._get_usage_data(days)
        if len(data) < 14:
            return []

        # 일별 집계
        daily = defaultdict(int)
        for row in data:
            daily[row["date"]] += row["calls"]

        values = list(daily.values())
        if len(values) < 7:
            return []

        # 평균 및 표준편차
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = math.sqrt(variance) if variance > 0 else 1

        # 이상치 탐지 (2 표준편차 이상)
        anomalies = []
        for date, calls in daily.items():
            z_score = (calls - mean) / std if std > 0 else 0
            if abs(z_score) > 2:
                anomaly_type = "급증" if z_score > 0 else "급감"
                anomalies.append({
                    "date": date,
                    "calls": calls,
                    "expected": round(mean, 1),
                    "z_score": round(z_score, 2),
                    "type": anomaly_type
                })
                self.insights.append(Insight(
                    id=f"ANOM_{date}",
                    category="anomaly",
                    title=f"{date} 사용량 {anomaly_type}",
                    description=f"평균 {mean:.0f}건 대비 {calls}건 ({anomaly_type})",
                    severity="warning",
                    metric_value=calls,
                    comparison_value=mean
                ))

        return anomalies

    # ==========================================================================
    # 리포트 생성
    # ==========================================================================

    def generate_insights(self, days: int = 30) -> List[Insight]:
        """전체 인사이트 생성"""
        self.insights = []

        self.analyze_usage_trend(days)
        self.analyze_performance(days)
        self.analyze_satisfaction(days)
        self.predict_usage(7)
        self.identify_anomalies(days)

        # 우선순위 정렬
        priority = {"critical": 0, "warning": 1, "info": 2}
        self.insights.sort(key=lambda x: priority.get(x.severity, 3))

        return self.insights

    def print_executive_report(self, days: int = 30):
        """경영진 리포트 출력"""
        print("\n" + "="*70)
        print("📊 DJSHS AI Agent System - 고급 분석 리포트")
        print(f"   기간: 최근 {days}일 | 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*70)

        # 인사이트 생성
        self.generate_insights(days)

        # 요약 통계
        usage_trend = self.analyze_usage_trend(days)
        performance = self.analyze_performance(days)
        satisfaction = self.analyze_satisfaction(days)
        predictions = self.predict_usage(7)

        print("\n📈 핵심 지표")
        print("-"*70)
        print(f"   사용량 추세: {usage_trend.get('trend', 'N/A')} ({usage_trend.get('change_percent', 0):+.1f}%)")
        print(f"   일평균 사용: {usage_trend.get('recent_avg_daily', 0):.1f}건")
        print(f"   문제 에이전트: {len(performance.get('problem_agents', []))}개")
        print(f"   평균 만족도: {satisfaction.get('overall_avg', 0):.1f}/5.0")

        # 예측
        if predictions.get("predictions"):
            week_pred = predictions["predictions"][-1]["predicted_calls"]
            print(f"   7일 후 예측: {week_pred:.0f}건/일")

        # 인사이트
        if self.insights:
            print(f"\n💡 주요 인사이트 ({len(self.insights)}건)")
            print("-"*70)

            for insight in self.insights[:10]:
                icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[insight.severity]
                print(f"\n   {icon} [{insight.category.upper()}] {insight.title}")
                print(f"      {insight.description}")
                if insight.action_items:
                    print(f"      → 권장 조치: {', '.join(insight.action_items[:2])}")

        # 권장 조치 요약
        actions = []
        for insight in self.insights:
            if insight.action_items:
                actions.extend(insight.action_items)

        if actions:
            print(f"\n🎯 권장 조치 사항")
            print("-"*70)
            unique_actions = list(dict.fromkeys(actions))[:5]
            for i, action in enumerate(unique_actions, 1):
                print(f"   {i}. {action}")

        print("\n" + "="*70)

    def export_report(self, output_path: str = None, days: int = 30) -> str:
        """JSON 리포트 내보내기"""
        if output_path is None:
            output_path = DATA_DIR / f"analytics_report_{datetime.now().strftime('%Y%m%d')}.json"

        self.generate_insights(days)

        report = {
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "usage_trend": self.analyze_usage_trend(days),
            "performance": self.analyze_performance(days),
            "satisfaction": self.analyze_satisfaction(days),
            "predictions": self.predict_usage(7),
            "anomalies": self.identify_anomalies(days),
            "insights": [
                {
                    "id": i.id,
                    "category": i.category,
                    "title": i.title,
                    "description": i.description,
                    "severity": i.severity,
                    "action_items": i.action_items
                }
                for i in self.insights
            ]
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return str(output_path)


# CLI 인터페이스
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DJSHS AI Agent 고급 분석")
    parser.add_argument("--report", "-r", action="store_true", help="경영진 리포트 출력")
    parser.add_argument("--days", "-d", type=int, default=30, help="분석 기간")
    parser.add_argument("--export", "-e", help="JSON 리포트 내보내기")
    parser.add_argument("--insights", "-i", action="store_true", help="인사이트만 출력")

    args = parser.parse_args()

    engine = AnalyticsEngine()

    if args.report:
        engine.print_executive_report(args.days)

    if args.insights:
        insights = engine.generate_insights(args.days)
        print(f"\n💡 생성된 인사이트 ({len(insights)}건)")
        for i in insights:
            icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[i.severity]
            print(f"  {icon} {i.title}: {i.description}")

    if args.export:
        path = engine.export_report(args.export, args.days)
        print(f"✅ 리포트 저장: {path}")

    if not any([args.report, args.insights, args.export]):
        engine.print_executive_report(args.days)
