"""
통계 계산 모듈

실험 데이터의 통계 분석을 수행합니다.
"""

import math
from typing import Dict, List, Optional, Tuple

from ..config import config
from ..parsers.data_models import ExperimentData
from ..sheets.formula_generator import FormulaGenerator


class StatisticsCalculator:
    """통계 계산 클래스"""

    def __init__(self, experiment_data: ExperimentData):
        self.data = experiment_data
        self.config = config
        self.formula_gen = FormulaGenerator(
            repetitions=experiment_data.repetitions,
            min_scale=experiment_data.min_scale,
        )
        self.t_value = self.config.get_t_value(experiment_data.repetitions)

    def calculate_mean(self, measurements: List[float]) -> float:
        """평균 계산"""
        if not measurements:
            return 0.0
        return sum(measurements) / len(measurements)

    def calculate_stdev(self, measurements: List[float]) -> float:
        """표본 표준편차 계산 (STDEV.S와 동일)"""
        if len(measurements) < 2:
            return 0.0

        mean = self.calculate_mean(measurements)
        variance = sum((x - mean) ** 2 for x in measurements) / (len(measurements) - 1)
        return math.sqrt(variance)

    def calculate_standard_error(self, measurements: List[float]) -> float:
        """표준 오차 계산 (평균의 표준 오차)"""
        if len(measurements) < 2:
            return 0.0

        stdev = self.calculate_stdev(measurements)
        return stdev / math.sqrt(len(measurements))

    def calculate_type_a_uncertainty(self, measurements: List[float]) -> float:
        """A형 불확도 계산 (통계적 불확도)

        u_A = t * s / sqrt(n)

        여기서:
        - t: t-값 (95% 신뢰수준)
        - s: 표본 표준편차
        - n: 측정 횟수
        """
        if len(measurements) < 2:
            return 0.0

        se = self.calculate_standard_error(measurements)
        return self.t_value * se

    def calculate_type_b_uncertainty(self) -> float:
        """B형 불확도 계산 (기기 불확도)

        u_B = d / (2 * sqrt(3))

        여기서:
        - d: 측정 도구 최소 눈금
        """
        return self.data.min_scale / (2 * math.sqrt(3))

    def calculate_uncertainty(self, measurements: List[float]) -> float:
        """합성 불확도 계산

        U = t * sqrt(u_A² + u_B²)
          = t * sqrt((s/√n)² + (d/(2√3))²)
        """
        if len(measurements) < 2:
            return self.t_value * self.calculate_type_b_uncertainty()

        se = self.calculate_standard_error(measurements)
        type_b = self.calculate_type_b_uncertainty()

        combined = math.sqrt(se**2 + type_b**2)
        return self.t_value * combined

    def calculate_relative_uncertainty(self, measurements: List[float]) -> float:
        """상대 불확도(%) 계산"""
        mean = self.calculate_mean(measurements)
        if mean == 0:
            return 0.0

        uncertainty = self.calculate_uncertainty(measurements)
        return (uncertainty / abs(mean)) * 100

    def get_statistics_for_condition(self, index: int) -> Dict[str, float]:
        """특정 조건의 모든 통계량 계산"""
        measurements = self.data.measurements[index]

        return {
            "mean": self.calculate_mean(measurements),
            "stdev": self.calculate_stdev(measurements),
            "standard_error": self.calculate_standard_error(measurements),
            "type_a_uncertainty": self.calculate_type_a_uncertainty(measurements),
            "type_b_uncertainty": self.calculate_type_b_uncertainty(),
            "uncertainty": self.calculate_uncertainty(measurements),
            "relative_uncertainty": self.calculate_relative_uncertainty(measurements),
            "min": min(measurements),
            "max": max(measurements),
            "range": max(measurements) - min(measurements),
            "count": len(measurements),
        }

    def get_all_statistics(self) -> List[Dict[str, float]]:
        """모든 조건의 통계량 계산"""
        return [
            self.get_statistics_for_condition(i)
            for i in range(len(self.data.measurements))
        ]

    def get_all_means(self) -> List[float]:
        """모든 조건의 평균 반환"""
        return [self.calculate_mean(m) for m in self.data.measurements]

    def get_all_uncertainties(self) -> List[float]:
        """모든 조건의 불확도 반환"""
        return [self.calculate_uncertainty(m) for m in self.data.measurements]

    def calculate_linear_regression(self) -> Optional[Dict[str, float]]:
        """선형 회귀 분석 (수치형 데이터만)

        y = mx + b

        Returns:
            slope (m), intercept (b), r_squared, correlation 등
        """
        if self.data.is_categorical:
            return None

        x = [float(v) for v in self.data.independent_values]
        y = self.get_all_means()

        n = len(x)
        if n < 2:
            return None

        # 평균
        x_mean = sum(x) / n
        y_mean = sum(y) / n

        # 공분산 및 분산
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        x_variance = sum((x[i] - x_mean) ** 2 for i in range(n))
        y_variance = sum((y[i] - y_mean) ** 2 for i in range(n))

        if x_variance == 0:
            return None

        # 기울기와 절편
        slope = numerator / x_variance
        intercept = y_mean - slope * x_mean

        # R² 계산
        y_pred = [slope * xi + intercept for xi in x]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))

        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # 상관계수
        correlation = math.sqrt(r_squared) if r_squared >= 0 else 0
        if slope < 0:
            correlation = -correlation

        # 기울기 불확도 계산
        if n > 2 and ss_res > 0:
            se_slope = math.sqrt(ss_res / ((n - 2) * x_variance))
        else:
            se_slope = 0

        return {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_squared,
            "correlation": correlation,
            "slope_uncertainty": se_slope,
            "equation": f"y = {slope:.4g}x + {intercept:.4g}" if intercept >= 0 else f"y = {slope:.4g}x - {abs(intercept):.4g}",
        }

    def summary(self) -> Dict[str, any]:
        """전체 데이터 요약"""
        all_stats = self.get_all_statistics()

        # 전체 측정값 통합
        all_measurements = [m for measurements in self.data.measurements for m in measurements]

        summary = {
            "experiment_name": self.data.experiment_name,
            "num_conditions": len(self.data.independent_values),
            "repetitions": self.data.repetitions,
            "total_measurements": len(all_measurements),
            "global_mean": self.calculate_mean(all_measurements),
            "global_stdev": self.calculate_stdev(all_measurements),
            "conditions": [],
        }

        for i, (ind_value, stats) in enumerate(zip(self.data.independent_values, all_stats)):
            summary["conditions"].append({
                "independent_value": ind_value,
                **stats,
            })

        # 선형 회귀 (수치형만)
        if not self.data.is_categorical:
            summary["linear_regression"] = self.calculate_linear_regression()

        return summary
