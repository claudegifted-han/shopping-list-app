"""
표 구조 생성 모듈

프롬프트 규칙에 따라 스프레드시트 표 구조를 생성합니다.

열 배치 규칙:
- A열: 공백 (변환용 예비)
- B열: 조작 변인
- C~G열: 반복 측정값 (5회 기준)
- H열: 평균 수식
- I열: 측정 불확도 수식

행 배치 규칙:
- 행1: 병합 헤더
- 행2: 세부 헤더 (1회, 2회, ..., 평균, 측정 불확도)
- 행3~: 데이터
"""

from typing import Any, Dict, List, Optional

from ..config import config
from ..parsers.data_models import ExperimentData
from .formula_generator import FormulaGenerator


class TableBuilder:
    """스프레드시트 표 구조 생성 클래스"""

    def __init__(self, experiment_data: ExperimentData):
        self.data = experiment_data
        self.formula_gen = FormulaGenerator(
            repetitions=experiment_data.repetitions,
            min_scale=experiment_data.min_scale,
        )
        self.config = config

    def build_table_structure(self) -> Dict[str, Any]:
        """전체 표 구조 생성"""
        return {
            "headers": self._build_headers(),
            "data_rows": self._build_data_rows(),
            "formatting": self._build_formatting(),
            "column_info": self._get_column_info(),
        }

    def _build_headers(self) -> Dict[str, List[Any]]:
        """헤더 행 생성"""
        repetitions = self.data.repetitions

        # 병합 헤더 (행1)
        # A: 공백, B: 조작변인명(단위), C~끝: 종속변인명(단위)
        merged_header = [""]  # A열 공백

        # B열: 조작 변인 헤더
        ind_header = self.data.independent_var
        if self.data.independent_unit:
            ind_header += f" ({self.data.independent_unit})"
        merged_header.append(ind_header)

        # C열~: 종속 변인 헤더 (첫 셀에만, 나머지는 병합 대상)
        dep_header = self.data.dependent_var
        if self.data.dependent_unit:
            dep_header += f" ({self.data.dependent_unit})"
        merged_header.append(dep_header)

        # 병합 대상 셀은 빈 문자열
        for _ in range(repetitions - 1 + 2):  # 측정값 나머지 + 평균 + 불확도
            merged_header.append("")

        # 세부 헤더 (행2)
        sub_header = ["", ""]  # A열 공백, B열 공백 (조작변인은 위에서 설명)

        # 측정 횟수 헤더
        for i in range(1, repetitions + 1):
            sub_header.append(f"{i}회")

        # 평균, 불확도 헤더
        sub_header.append("평균")
        sub_header.append("측정 불확도")

        return {
            "merged": merged_header,
            "sub": sub_header,
        }

    def _build_data_rows(self) -> List[List[Any]]:
        """데이터 행 생성 (수식 포함)"""
        rows = []
        data_start_row = self.config.ROW_LAYOUT["data_start"]

        for i, (ind_value, measurements) in enumerate(
            zip(self.data.independent_values, self.data.measurements)
        ):
            current_row = data_start_row + i
            row = [""]  # A열 공백

            # B열: 조작 변인 값
            row.append(ind_value)

            # C~열: 측정값
            for measurement in measurements:
                row.append(measurement)

            # 평균 수식
            row.append(self.formula_gen.average_formula(current_row))

            # 불확도 수식
            row.append(self.formula_gen.uncertainty_formula(current_row))

            rows.append(row)

        return rows

    def _build_formatting(self) -> Dict[str, Any]:
        """서식 정보 생성"""
        repetitions = self.data.repetitions
        last_data_col = self.formula_gen.get_uncertainty_column()
        num_data_rows = len(self.data.independent_values)

        return {
            "header_range": {
                "start": "A1",
                "end": f"{last_data_col}2",
                "background_color": self.config.HEADER_BACKGROUND_COLOR,
                "font_weight": self.config.HEADER_FONT_WEIGHT,
                "horizontal_alignment": "center",
            },
            "merge_cells": [
                # 종속 변인 헤더 병합 (C1 ~ I1)
                {
                    "start": "C1",
                    "end": f"{last_data_col}1",
                }
            ],
            "number_format": {
                # 측정값 및 계산값 소수점 형식
                "range": f"C3:{last_data_col}{2 + num_data_rows}",
                "format": self._determine_number_format(),
            },
            "column_widths": self._get_column_widths(),
        }

    def _get_column_info(self) -> Dict[str, str]:
        """열 정보 반환"""
        return {
            "empty": "A",
            "independent": "B",
            "measurements": self.formula_gen.get_measurement_columns(),
            "average": self.formula_gen.get_average_column(),
            "uncertainty": self.formula_gen.get_uncertainty_column(),
        }

    def _determine_number_format(self) -> str:
        """측정 도구 최소 눈금에 따른 숫자 형식 결정"""
        min_scale = self.data.min_scale

        if min_scale >= 1:
            return "0"
        elif min_scale >= 0.1:
            return "0.0"
        elif min_scale >= 0.01:
            return "0.00"
        elif min_scale >= 0.001:
            return "0.000"
        else:
            return "0.0000"

    def _get_column_widths(self) -> Dict[str, int]:
        """열 너비 설정"""
        widths = {
            "A": 30,  # 공백 (좁게)
            "B": 100,  # 조작 변인
        }

        # 측정값 열
        for col in self.formula_gen.get_measurement_columns():
            widths[col] = 80

        # 평균, 불확도 열
        widths[self.formula_gen.get_average_column()] = 80
        widths[self.formula_gen.get_uncertainty_column()] = 100

        return widths

    def get_zapier_instructions(self) -> Dict[str, Any]:
        """Zapier MCP 도구 사용을 위한 지침 생성"""
        table_structure = self.build_table_structure()

        return {
            "spreadsheet_title": f"{self.data.experiment_name} 데이터",
            "worksheet_title": "실험 데이터",
            "steps": [
                {
                    "step": 1,
                    "action": "create_spreadsheet",
                    "description": "새 스프레드시트 생성",
                    "params": {
                        "title": f"{self.data.experiment_name} 데이터",
                    },
                },
                {
                    "step": 2,
                    "action": "create_multiple_rows",
                    "description": "헤더 및 데이터 입력",
                    "rows": [
                        table_structure["headers"]["merged"],
                        table_structure["headers"]["sub"],
                        *table_structure["data_rows"],
                    ],
                },
                {
                    "step": 3,
                    "action": "format_header",
                    "description": "헤더 서식 적용 (연한 노란색 배경)",
                    "formatting": table_structure["formatting"]["header_range"],
                },
                {
                    "step": 4,
                    "action": "format_numbers",
                    "description": "숫자 형식 적용",
                    "formatting": table_structure["formatting"]["number_format"],
                },
            ],
            "notes": [
                "A열은 단위 변환용 예비 열로 비워둡니다.",
                "셀 병합은 Zapier에서 지원하지 않아 수동으로 진행해야 합니다.",
                f"병합 대상: C1:{table_structure['column_info']['uncertainty']}1",
            ],
            "formulas": {
                "average": self.formula_gen.average_formula(3),
                "uncertainty": self.formula_gen.uncertainty_formula(3),
            },
        }

    def to_csv_format(self) -> str:
        """CSV 형식으로 변환"""
        table = self.build_table_structure()
        lines = []

        # 헤더
        lines.append(",".join(str(cell) for cell in table["headers"]["merged"]))
        lines.append(",".join(str(cell) for cell in table["headers"]["sub"]))

        # 데이터
        for row in table["data_rows"]:
            lines.append(",".join(str(cell) for cell in row))

        return "\n".join(lines)

    def get_raw_data_for_sheets(self) -> List[List[Any]]:
        """Google Sheets API용 원시 데이터 반환

        수식을 포함하지 않은 순수 데이터만 반환
        """
        rows = []

        # 헤더 행
        headers = self._build_headers()
        rows.append(headers["merged"])
        rows.append(headers["sub"])

        # 데이터 행 (수식 제외)
        data_start_row = self.config.ROW_LAYOUT["data_start"]

        for i, (ind_value, measurements) in enumerate(
            zip(self.data.independent_values, self.data.measurements)
        ):
            row = [""]  # A열 공백
            row.append(ind_value)  # B열: 조작 변인

            for measurement in measurements:
                row.append(measurement)

            # 평균과 불확도는 수식 대신 계산된 값으로 대체
            from ..analysis.statistics import StatisticsCalculator
            calc = StatisticsCalculator(self.data)

            avg = calc.calculate_mean(measurements)
            unc = calc.calculate_uncertainty(measurements)

            row.append(avg)
            row.append(unc)

            rows.append(row)

        return rows
