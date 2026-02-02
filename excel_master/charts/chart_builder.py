"""
차트 생성 모듈

matplotlib을 사용하여 실험 데이터 차트를 생성합니다.

차트 유형:
- 분산형(XY Scatter): 수치형 조작변인
- 막대형(Bar): 범주형 조작변인

기능:
- 오차막대: 측정 불확도 값
- 추세선: 수식 + R² 값 표시
"""

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from ..config import config
from ..parsers.data_models import ExperimentData
from ..analysis.statistics import StatisticsCalculator


class ChartBuilder:
    """matplotlib 차트 생성 클래스"""

    def __init__(self, experiment_data: ExperimentData):
        self.data = experiment_data
        self.config = config
        self.stats = StatisticsCalculator(experiment_data)

        # matplotlib 지연 임포트
        self._plt = None
        self._mpl = None

    def _import_matplotlib(self):
        """matplotlib 지연 임포트"""
        if self._plt is None:
            import matplotlib
            matplotlib.use('Agg')  # GUI 없는 환경용
            import matplotlib.pyplot as plt

            # 한글 폰트 설정 시도
            try:
                plt.rcParams['font.family'] = ['DejaVu Sans', 'Malgun Gothic', 'AppleGothic', 'sans-serif']
            except Exception:
                pass

            plt.rcParams['axes.unicode_minus'] = False

            self._plt = plt
            self._mpl = matplotlib

    @property
    def plt(self):
        self._import_matplotlib()
        return self._plt

    def create_chart(
        self,
        output_path: Optional[str] = None,
        chart_type: Optional[str] = None,
        show_trendline: bool = True,
        show_equation: bool = True,
        show_r_squared: bool = True,
        title: Optional[str] = None,
        figsize: Optional[Tuple[int, int]] = None,
    ) -> Union[str, bytes]:
        """차트 생성

        Args:
            output_path: 저장 경로 (None이면 바이트 반환)
            chart_type: 차트 유형 ("scatter" 또는 "bar", None이면 자동)
            show_trendline: 추세선 표시 여부
            show_equation: 추세선 수식 표시 여부
            show_r_squared: R² 값 표시 여부
            title: 차트 제목 (None이면 자동)
            figsize: 그림 크기

        Returns:
            파일 경로 또는 이미지 바이트
        """
        # 차트 유형 자동 결정
        if chart_type is None:
            chart_type = "bar" if self.data.is_categorical else "scatter"

        if chart_type == "scatter":
            return self._create_scatter_chart(
                output_path=output_path,
                show_trendline=show_trendline,
                show_equation=show_equation,
                show_r_squared=show_r_squared,
                title=title,
                figsize=figsize,
            )
        else:
            return self._create_bar_chart(
                output_path=output_path,
                title=title,
                figsize=figsize,
            )

    def _create_scatter_chart(
        self,
        output_path: Optional[str] = None,
        show_trendline: bool = True,
        show_equation: bool = True,
        show_r_squared: bool = True,
        title: Optional[str] = None,
        figsize: Optional[Tuple[int, int]] = None,
    ) -> Union[str, bytes]:
        """분산형(XY Scatter) 차트 생성"""
        plt = self.plt

        # 데이터 준비
        x_values = [float(v) for v in self.data.independent_values]
        y_means = self.stats.get_all_means()
        y_uncertainties = self.stats.get_all_uncertainties()

        # 그림 생성
        fig_size = figsize or self.config.CHART_FIGURE_SIZE
        fig, ax = plt.subplots(figsize=fig_size, dpi=self.config.CHART_DPI)

        # 데이터 포인트 + 오차막대
        ax.errorbar(
            x_values, y_means, yerr=y_uncertainties,
            fmt='o', capsize=5, capthick=1.5, elinewidth=1.5,
            markersize=8, color='#2E86AB', ecolor='#A23B72',
            label='측정값'
        )

        # 추세선
        if show_trendline and len(x_values) >= 2:
            self._add_trendline(
                ax, x_values, y_means,
                show_equation=show_equation,
                show_r_squared=show_r_squared,
            )

        # 축 레이블
        x_label = self.data.independent_var
        if self.data.independent_unit:
            x_label += f" ({self.data.independent_unit})"
        ax.set_xlabel(x_label, fontsize=12)

        y_label = self.data.dependent_var
        if self.data.dependent_unit:
            y_label += f" ({self.data.dependent_unit})"
        ax.set_ylabel(y_label, fontsize=12)

        # 제목
        chart_title = title or f"{self.data.experiment_name}"
        ax.set_title(chart_title, fontsize=14, fontweight='bold')

        # 범례
        ax.legend(loc='best')

        # 그리드
        ax.grid(True, alpha=0.3)

        # 여백 조정
        plt.tight_layout()

        return self._save_or_return(fig, output_path)

    def _create_bar_chart(
        self,
        output_path: Optional[str] = None,
        title: Optional[str] = None,
        figsize: Optional[Tuple[int, int]] = None,
    ) -> Union[str, bytes]:
        """막대형(Bar) 차트 생성"""
        plt = self.plt

        # 데이터 준비
        x_labels = [str(v) for v in self.data.independent_values]
        y_means = self.stats.get_all_means()
        y_uncertainties = self.stats.get_all_uncertainties()

        # 그림 생성
        fig_size = figsize or self.config.CHART_FIGURE_SIZE
        fig, ax = plt.subplots(figsize=fig_size, dpi=self.config.CHART_DPI)

        # 막대 위치
        x_pos = np.arange(len(x_labels))

        # 막대 그래프 + 오차막대
        bars = ax.bar(
            x_pos, y_means, yerr=y_uncertainties,
            capsize=5, color='#2E86AB', edgecolor='#1A5276',
            alpha=0.8, error_kw={'elinewidth': 1.5, 'capthick': 1.5, 'ecolor': '#A23B72'}
        )

        # x축 레이블
        ax.set_xticks(x_pos)
        ax.set_xticklabels(x_labels, rotation=45 if len(x_labels) > 5 else 0, ha='right')

        # 축 레이블
        x_label = self.data.independent_var
        if self.data.independent_unit:
            x_label += f" ({self.data.independent_unit})"
        ax.set_xlabel(x_label, fontsize=12)

        y_label = self.data.dependent_var
        if self.data.dependent_unit:
            y_label += f" ({self.data.dependent_unit})"
        ax.set_ylabel(y_label, fontsize=12)

        # 제목
        chart_title = title or f"{self.data.experiment_name}"
        ax.set_title(chart_title, fontsize=14, fontweight='bold')

        # y축 0부터 시작
        ax.set_ylim(bottom=0)

        # 그리드 (가로선만)
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)

        # 여백 조정
        plt.tight_layout()

        return self._save_or_return(fig, output_path)

    def _add_trendline(
        self,
        ax,
        x_values: List[float],
        y_values: List[float],
        show_equation: bool = True,
        show_r_squared: bool = True,
        degree: int = 1,
    ):
        """추세선 추가"""
        x = np.array(x_values)
        y = np.array(y_values)

        # 다항식 피팅
        coefficients = np.polyfit(x, y, degree)
        poly = np.poly1d(coefficients)

        # 추세선 x 범위
        x_line = np.linspace(min(x) * 0.95, max(x) * 1.05, 100)
        y_line = poly(x_line)

        # 추세선 그리기
        ax.plot(x_line, y_line, '--', color='#E74C3C', linewidth=1.5, label='추세선')

        # R² 계산
        y_pred = poly(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # 수식 및 R² 표시
        if show_equation or show_r_squared:
            text_parts = []

            if show_equation:
                if degree == 1:
                    # 선형: y = mx + b
                    m, b = coefficients
                    sign = '+' if b >= 0 else '-'
                    text_parts.append(f"y = {m:.4g}x {sign} {abs(b):.4g}")
                else:
                    # 다항식
                    terms = []
                    for i, coef in enumerate(coefficients):
                        power = degree - i
                        if power == 0:
                            terms.append(f"{coef:.4g}")
                        elif power == 1:
                            terms.append(f"{coef:.4g}x")
                        else:
                            terms.append(f"{coef:.4g}x^{power}")
                    text_parts.append("y = " + " + ".join(terms))

            if show_r_squared:
                text_parts.append(f"R² = {r_squared:.4f}")

            # 텍스트 위치 (우상단)
            text = "\n".join(text_parts)
            ax.text(
                0.95, 0.95, text,
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment='top',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )

    def _save_or_return(self, fig, output_path: Optional[str]) -> Union[str, bytes]:
        """그림 저장 또는 바이트 반환"""
        plt = self.plt

        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            return str(path.absolute())
        else:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
            plt.close(fig)
            buf.seek(0)
            return buf.getvalue()

    def create_residual_plot(
        self,
        output_path: Optional[str] = None,
        figsize: Optional[Tuple[int, int]] = None,
    ) -> Union[str, bytes]:
        """잔차 플롯 생성 (추세선 적합도 확인용)"""
        if self.data.is_categorical:
            raise ValueError("범주형 데이터는 잔차 플롯을 생성할 수 없습니다.")

        plt = self.plt

        # 데이터 준비
        x_values = np.array([float(v) for v in self.data.independent_values])
        y_means = np.array(self.stats.get_all_means())

        # 선형 피팅
        coefficients = np.polyfit(x_values, y_means, 1)
        poly = np.poly1d(coefficients)
        y_pred = poly(x_values)

        # 잔차 계산
        residuals = y_means - y_pred

        # 그림 생성
        fig_size = figsize or self.config.CHART_FIGURE_SIZE
        fig, ax = plt.subplots(figsize=fig_size, dpi=self.config.CHART_DPI)

        # 잔차 플롯
        ax.scatter(x_values, residuals, color='#2E86AB', s=50)
        ax.axhline(y=0, color='#E74C3C', linestyle='--', linewidth=1)

        # 축 레이블
        x_label = self.data.independent_var
        if self.data.independent_unit:
            x_label += f" ({self.data.independent_unit})"
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel("잔차", fontsize=12)

        # 제목
        ax.set_title(f"{self.data.experiment_name} - 잔차 플롯", fontsize=14, fontweight='bold')

        # 그리드
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        return self._save_or_return(fig, output_path)

    def get_google_sheets_chart_instructions(self) -> Dict[str, Any]:
        """Google Sheets 내장 차트 생성 안내"""
        chart_type = "SCATTER" if not self.data.is_categorical else "COLUMN"

        return {
            "note": "Zapier MCP는 차트 생성을 지원하지 않습니다. Google Sheets에서 수동으로 차트를 생성하세요.",
            "instructions": [
                "1. 데이터 범위 선택 (B열~I열, 헤더 포함)",
                "2. 삽입 > 차트 메뉴 선택",
                f"3. 차트 유형: {chart_type} 선택",
                "4. X축: 조작 변인 열(B열) 선택",
                "5. Y축: 평균 열(H열) 선택",
                "6. 오차막대: 측정 불확도 열(I열)로 설정",
                "7. 추세선 추가 (수식 + R² 표시 체크)",
            ],
            "chart_settings": {
                "chart_type": chart_type,
                "x_axis_column": "B",
                "y_axis_column": self.stats.formula_gen.get_average_column(),
                "error_bar_column": self.stats.formula_gen.get_uncertainty_column(),
                "show_trendline": not self.data.is_categorical,
                "show_r_squared": not self.data.is_categorical,
            },
        }
