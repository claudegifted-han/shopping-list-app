"""
분석 보고서 생성 모듈

실험 데이터 분석 결과를 보고서 형태로 생성합니다.
"""

from typing import Any, Dict, List, Optional

from ..config import config
from ..parsers.data_models import ExperimentData
from ..utils import round_to_uncertainty, format_with_uncertainty
from .statistics import StatisticsCalculator


class ReportGenerator:
    """분석 보고서 생성 클래스"""

    def __init__(self, experiment_data: ExperimentData):
        self.data = experiment_data
        self.stats = StatisticsCalculator(experiment_data)
        self.config = config

    def generate_summary_report(self) -> str:
        """요약 보고서 생성"""
        summary = self.stats.summary()
        lines = []

        # 제목
        lines.append(f"# {summary['experiment_name']} 분석 보고서")
        lines.append("")

        # 실험 개요
        lines.append("## 실험 개요")
        lines.append(f"- 조작 변인: {self.data.independent_var} ({self.data.independent_unit})")
        lines.append(f"- 종속 변인: {self.data.dependent_var} ({self.data.dependent_unit})")
        lines.append(f"- 조건 수: {summary['num_conditions']}개")
        lines.append(f"- 반복 측정: {summary['repetitions']}회")
        lines.append(f"- 총 측정 횟수: {summary['total_measurements']}회")
        lines.append(f"- 측정 도구 최소 눈금: {self.data.min_scale}")
        lines.append("")

        # 데이터 요약 표
        lines.append("## 측정 결과 요약")
        lines.append("")
        self._add_summary_table(lines, summary)
        lines.append("")

        # 회귀 분석 (수치형만)
        if not self.data.is_categorical and summary.get("linear_regression"):
            reg = summary["linear_regression"]
            lines.append("## 회귀 분석")
            lines.append(f"- 추세선 방정식: {reg['equation']}")
            lines.append(f"- 결정계수(R²): {reg['r_squared']:.4f}")
            lines.append(f"- 상관계수: {reg['correlation']:.4f}")
            lines.append(f"- 기울기 불확도: ±{reg['slope_uncertainty']:.4g}")
            lines.append("")

        # 불확도 분석
        lines.append("## 불확도 분석")
        lines.append(f"- t-값: {self.stats.t_value} (95% 신뢰수준, 자유도 {self.data.repetitions - 1})")
        lines.append(f"- B형 불확도 (기기): {self.stats.calculate_type_b_uncertainty():.4g}")
        lines.append("")

        self._add_uncertainty_table(lines, summary)
        lines.append("")

        # 결론 및 제안
        lines.append("## 분석 소견")
        self._add_analysis_notes(lines, summary)

        return "\n".join(lines)

    def _add_summary_table(self, lines: List[str], summary: Dict[str, Any]):
        """요약 표 추가"""
        # 헤더
        headers = [
            self.data.independent_var,
            f"평균 ({self.data.dependent_unit})",
            f"불확도 ({self.data.dependent_unit})",
            "상대 불확도 (%)"
        ]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # 데이터 행
        for cond in summary["conditions"]:
            ind_val = cond["independent_value"]
            mean = cond["mean"]
            unc = cond["uncertainty"]
            rel_unc = cond["relative_uncertainty"]

            # 유효숫자 처리
            mean_str, unc_str = format_with_uncertainty(mean, unc)

            row = [
                str(ind_val),
                mean_str,
                unc_str,
                f"{rel_unc:.1f}"
            ]
            lines.append("| " + " | ".join(row) + " |")

    def _add_uncertainty_table(self, lines: List[str], summary: Dict[str, Any]):
        """불확도 상세 표 추가"""
        headers = [
            self.data.independent_var,
            "표준편차",
            "A형 불확도",
            "합성 불확도"
        ]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for cond in summary["conditions"]:
            row = [
                str(cond["independent_value"]),
                f"{cond['stdev']:.4g}",
                f"{cond['type_a_uncertainty']:.4g}",
                f"{cond['uncertainty']:.4g}"
            ]
            lines.append("| " + " | ".join(row) + " |")

    def _add_analysis_notes(self, lines: List[str], summary: Dict[str, Any]):
        """분석 소견 추가"""
        # 상대 불확도 평가
        avg_rel_unc = sum(c["relative_uncertainty"] for c in summary["conditions"]) / len(summary["conditions"])

        if avg_rel_unc < 5:
            lines.append(f"- 평균 상대 불확도 {avg_rel_unc:.1f}%로 측정 정밀도가 양호합니다.")
        elif avg_rel_unc < 10:
            lines.append(f"- 평균 상대 불확도 {avg_rel_unc:.1f}%로 측정 정밀도가 보통입니다.")
        else:
            lines.append(f"- 평균 상대 불확도 {avg_rel_unc:.1f}%로 측정 정밀도 개선이 필요합니다.")

        # 회귀 분석 평가
        if not self.data.is_categorical and summary.get("linear_regression"):
            reg = summary["linear_regression"]
            r_sq = reg["r_squared"]

            if r_sq >= 0.99:
                lines.append(f"- R² = {r_sq:.4f}로 매우 강한 선형 관계를 보입니다.")
            elif r_sq >= 0.95:
                lines.append(f"- R² = {r_sq:.4f}로 강한 선형 관계를 보입니다.")
            elif r_sq >= 0.8:
                lines.append(f"- R² = {r_sq:.4f}로 선형 관계가 있으나 다른 요인의 영향이 있을 수 있습니다.")
            else:
                lines.append(f"- R² = {r_sq:.4f}로 선형 관계가 약합니다. 비선형 모델을 고려해 보세요.")

        # 이상치 확인
        max_rel_unc = max(c["relative_uncertainty"] for c in summary["conditions"])
        min_rel_unc = min(c["relative_uncertainty"] for c in summary["conditions"])

        if max_rel_unc > min_rel_unc * 3:
            outlier_cond = max(summary["conditions"], key=lambda x: x["relative_uncertainty"])
            lines.append(f"- 조건 {outlier_cond['independent_value']}에서 상대 불확도가 높습니다. 해당 조건의 측정을 재검토하세요.")

    def generate_data_table(self) -> str:
        """데이터 테이블 생성 (마크다운)"""
        lines = []

        # 헤더
        headers = [self.data.independent_var]
        for i in range(1, self.data.repetitions + 1):
            headers.append(f"{i}회")
        headers.extend(["평균", "불확도"])

        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # 데이터 행
        all_stats = self.stats.get_all_statistics()

        for i, (ind_value, measurements, stats) in enumerate(
            zip(self.data.independent_values, self.data.measurements, all_stats)
        ):
            mean_str, unc_str = format_with_uncertainty(stats["mean"], stats["uncertainty"])

            row = [str(ind_value)]
            row.extend([str(m) for m in measurements])
            row.extend([mean_str, unc_str])

            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)

    def generate_json_report(self) -> Dict[str, Any]:
        """JSON 형식 보고서 생성"""
        summary = self.stats.summary()

        # 유효숫자 처리된 결과
        processed_conditions = []
        for cond in summary["conditions"]:
            mean_str, unc_str = format_with_uncertainty(cond["mean"], cond["uncertainty"])
            processed_conditions.append({
                **cond,
                "mean_formatted": mean_str,
                "uncertainty_formatted": unc_str,
                "result": f"{mean_str} ± {unc_str}",
            })

        return {
            "experiment": {
                "name": self.data.experiment_name,
                "independent_var": self.data.independent_var,
                "independent_unit": self.data.independent_unit,
                "dependent_var": self.data.dependent_var,
                "dependent_unit": self.data.dependent_unit,
                "repetitions": self.data.repetitions,
                "min_scale": self.data.min_scale,
            },
            "statistics": {
                "num_conditions": summary["num_conditions"],
                "total_measurements": summary["total_measurements"],
                "global_mean": summary["global_mean"],
                "global_stdev": summary["global_stdev"],
            },
            "conditions": processed_conditions,
            "linear_regression": summary.get("linear_regression"),
            "uncertainty_info": {
                "t_value": self.stats.t_value,
                "degrees_of_freedom": self.data.repetitions - 1,
                "confidence_level": "95%",
                "type_b_uncertainty": self.stats.calculate_type_b_uncertainty(),
            },
        }

    def generate_latex_table(self) -> str:
        """LaTeX 형식 테이블 생성"""
        lines = []

        # 테이블 시작
        num_cols = self.data.repetitions + 4  # 조작변인 + 측정값들 + 평균 + 불확도
        lines.append("\\begin{table}[htbp]")
        lines.append("\\centering")
        lines.append(f"\\caption{{{self.data.experiment_name} 측정 결과}}")
        lines.append("\\begin{tabular}{" + "c" * num_cols + "}")
        lines.append("\\hline")

        # 헤더
        headers = [f"{self.data.independent_var} ({self.data.independent_unit})"]
        for i in range(1, self.data.repetitions + 1):
            headers.append(f"{i}회")
        headers.extend(["평균", "불확도"])
        lines.append(" & ".join(headers) + " \\\\")
        lines.append("\\hline")

        # 데이터
        all_stats = self.stats.get_all_statistics()

        for ind_value, measurements, stats in zip(
            self.data.independent_values, self.data.measurements, all_stats
        ):
            mean_str, unc_str = format_with_uncertainty(stats["mean"], stats["uncertainty"])

            row = [str(ind_value)]
            row.extend([str(m) for m in measurements])
            row.extend([mean_str, unc_str])

            lines.append(" & ".join(row) + " \\\\")

        lines.append("\\hline")
        lines.append("\\end{tabular}")
        lines.append("\\end{table}")

        return "\n".join(lines)
