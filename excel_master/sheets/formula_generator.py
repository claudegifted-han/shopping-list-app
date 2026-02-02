"""
수식 생성 모듈

Google Sheets용 수식을 생성합니다.

수식 규칙:
- 평균: =AVERAGE(C{row}:G{row})
- 불확도: =2.78*SQRT((STDEV.S(C{row}:G{row})/SQRT(5))^2 + (d/(2*SQRT(3)))^2)

t-값 (95% 신뢰수준):
- 5회: 2.78 (자유도 4)
- 4회: 3.18 (자유도 3)
- 3회: 4.30 (자유도 2)
"""

from typing import List

from ..config import config


class FormulaGenerator:
    """Google Sheets 수식 생성 클래스"""

    def __init__(self, repetitions: int = 5, min_scale: float = 0.01):
        self.repetitions = repetitions
        self.min_scale = min_scale
        self.config = config
        self.t_value = self.config.get_t_value(repetitions)

        # 열 정보 계산
        self._measurement_cols = self.config.get_measurement_columns(repetitions)
        self._average_col = self.config.get_average_column(repetitions)
        self._uncertainty_col = self.config.get_uncertainty_column(repetitions)

    def get_measurement_columns(self) -> List[str]:
        """측정값 열 목록 반환"""
        return self._measurement_cols

    def get_average_column(self) -> str:
        """평균 열 반환"""
        return self._average_col

    def get_uncertainty_column(self) -> str:
        """불확도 열 반환"""
        return self._uncertainty_col

    def average_formula(self, row: int) -> str:
        """평균 수식 생성

        Args:
            row: 행 번호

        Returns:
            =AVERAGE(C{row}:G{row}) 형식의 수식
        """
        start_col = self._measurement_cols[0]
        end_col = self._measurement_cols[-1]
        return f"=AVERAGE({start_col}{row}:{end_col}{row})"

    def uncertainty_formula(self, row: int) -> str:
        """측정 불확도 수식 생성

        합성 불확도 공식:
        U = t * sqrt((s/√n)² + (d/(2√3))²)

        여기서:
        - t: t-값 (95% 신뢰수준)
        - s: 표준편차 (STDEV.S)
        - n: 반복 횟수
        - d: 측정 도구 최소 눈금

        Args:
            row: 행 번호

        Returns:
            불확도 수식
        """
        start_col = self._measurement_cols[0]
        end_col = self._measurement_cols[-1]
        n = self.repetitions
        t = self.t_value
        d = self.min_scale

        # 수식 구성요소
        range_ref = f"{start_col}{row}:{end_col}{row}"
        stdev_part = f"STDEV.S({range_ref})/SQRT({n})"
        instrument_part = f"{d}/(2*SQRT(3))"

        formula = f"={t}*SQRT(({stdev_part})^2+({instrument_part})^2)"
        return formula

    def uncertainty_formula_with_cell_ref(self, row: int, min_scale_cell: str) -> str:
        """최소 눈금을 셀 참조로 하는 불확도 수식

        Args:
            row: 행 번호
            min_scale_cell: 최소 눈금이 입력된 셀 (예: "K1")

        Returns:
            불확도 수식 (최소 눈금이 셀 참조)
        """
        start_col = self._measurement_cols[0]
        end_col = self._measurement_cols[-1]
        n = self.repetitions
        t = self.t_value

        range_ref = f"{start_col}{row}:{end_col}{row}"
        stdev_part = f"STDEV.S({range_ref})/SQRT({n})"
        instrument_part = f"${min_scale_cell}/(2*SQRT(3))"

        formula = f"={t}*SQRT(({stdev_part})^2+({instrument_part})^2)"
        return formula

    def relative_error_formula(self, row: int) -> str:
        """상대 불확도(%) 수식 생성

        상대 불확도 = (측정 불확도 / 평균) * 100

        Args:
            row: 행 번호

        Returns:
            상대 불확도 수식
        """
        avg_col = self._average_col
        unc_col = self._uncertainty_col
        return f"=({unc_col}{row}/{avg_col}{row})*100"

    def count_formula(self, row: int) -> str:
        """유효 데이터 개수 수식

        Args:
            row: 행 번호

        Returns:
            COUNT 수식
        """
        start_col = self._measurement_cols[0]
        end_col = self._measurement_cols[-1]
        return f"=COUNT({start_col}{row}:{end_col}{row})"

    def min_formula(self, row: int) -> str:
        """최소값 수식

        Args:
            row: 행 번호

        Returns:
            MIN 수식
        """
        start_col = self._measurement_cols[0]
        end_col = self._measurement_cols[-1]
        return f"=MIN({start_col}{row}:{end_col}{row})"

    def max_formula(self, row: int) -> str:
        """최대값 수식

        Args:
            row: 행 번호

        Returns:
            MAX 수식
        """
        start_col = self._measurement_cols[0]
        end_col = self._measurement_cols[-1]
        return f"=MAX({start_col}{row}:{end_col}{row})"

    def stdev_formula(self, row: int) -> str:
        """표준편차 수식

        Args:
            row: 행 번호

        Returns:
            STDEV.S 수식
        """
        start_col = self._measurement_cols[0]
        end_col = self._measurement_cols[-1]
        return f"=STDEV.S({start_col}{row}:{end_col}{row})"

    def get_all_formulas(self, row: int) -> dict:
        """모든 수식 한번에 반환

        Args:
            row: 행 번호

        Returns:
            수식 딕셔너리
        """
        return {
            "average": self.average_formula(row),
            "uncertainty": self.uncertainty_formula(row),
            "relative_error": self.relative_error_formula(row),
            "stdev": self.stdev_formula(row),
            "min": self.min_formula(row),
            "max": self.max_formula(row),
            "count": self.count_formula(row),
        }

    def get_formula_explanations(self) -> dict:
        """수식 설명 반환"""
        return {
            "average": {
                "formula": "=AVERAGE(범위)",
                "description": "측정값들의 산술 평균",
            },
            "uncertainty": {
                "formula": f"={self.t_value}*SQRT((STDEV.S(범위)/SQRT({self.repetitions}))^2+({self.min_scale}/(2*SQRT(3)))^2)",
                "description": f"합성 불확도 (t-값: {self.t_value}, 반복: {self.repetitions}회, 최소눈금: {self.min_scale})",
                "components": {
                    "t_value": f"{self.t_value} (95% 신뢰수준, 자유도 {self.repetitions - 1})",
                    "statistical": "STDEV.S(범위)/SQRT(n) - A형 불확도 (통계적)",
                    "instrumental": f"{self.min_scale}/(2*SQRT(3)) - B형 불확도 (기기)",
                },
            },
        }
