"""
데이터 파서 모듈

대화형 입력 및 파일(CSV/Excel) 파싱을 담당합니다.
"""

import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .data_models import ExperimentData


class DataParser:
    """실험 데이터 파싱 클래스"""

    def __init__(self):
        self.supported_extensions = [".csv", ".xlsx", ".xls"]

    def parse_file(self, file_path: str) -> ExperimentData:
        """파일에서 실험 데이터 파싱"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        extension = path.suffix.lower()

        if extension == ".csv":
            return self._parse_csv(path)
        elif extension in [".xlsx", ".xls"]:
            return self._parse_excel(path)
        else:
            raise ValueError(
                f"지원하지 않는 파일 형식입니다: {extension}. "
                f"지원 형식: {', '.join(self.supported_extensions)}"
            )

    def _parse_csv(self, path: Path) -> ExperimentData:
        """CSV 파일 파싱"""
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        return self._parse_table_data(rows, str(path))

    def _parse_excel(self, path: Path) -> ExperimentData:
        """Excel 파일 파싱"""
        try:
            import openpyxl
        except ImportError:
            raise ImportError("Excel 파일 파싱을 위해 openpyxl이 필요합니다: pip install openpyxl")

        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.active

        rows = []
        for row in ws.iter_rows():
            rows.append([cell.value for cell in row])

        return self._parse_table_data(rows, str(path))

    def _parse_table_data(
        self, rows: List[List[Any]], source_file: Optional[str] = None
    ) -> ExperimentData:
        """테이블 형식 데이터 파싱

        예상 형식:
        - 행1: 메타데이터 (실험명, 조작변인명, 종속변인명 등)
        - 행2: 헤더 (조작변인, 1회, 2회, ..., n회)
        - 행3~: 데이터

        또는 간단한 형식:
        - 행1: 헤더 (조작변인, 1회, 2회, ..., n회)
        - 행2~: 데이터
        """
        if not rows or len(rows) < 2:
            raise ValueError("데이터가 부족합니다. 최소 2행 이상 필요합니다.")

        # 메타데이터 추출 시도
        metadata = self._extract_metadata(rows)

        # 데이터 시작 행 결정
        data_start = metadata.get("data_start_row", 1)
        header_row = rows[data_start - 1] if data_start > 0 else rows[0]
        data_rows = rows[data_start:]

        # 반복 횟수 결정
        repetitions = self._detect_repetitions(header_row)

        # 데이터 파싱
        independent_values = []
        measurements = []

        for row in data_rows:
            if not row or all(cell is None or cell == "" for cell in row):
                continue

            # 첫 번째 열: 조작 변인 값
            ind_value = row[0]
            if ind_value is None or ind_value == "":
                continue

            independent_values.append(self._parse_value(ind_value))

            # 나머지 열: 측정값
            measurement = []
            for i in range(1, repetitions + 1):
                if i < len(row) and row[i] is not None:
                    measurement.append(float(row[i]))
                else:
                    measurement.append(0.0)
            measurements.append(measurement)

        return ExperimentData(
            experiment_name=metadata.get("experiment_name", "실험"),
            independent_var=metadata.get("independent_var", "조작 변인"),
            independent_unit=metadata.get("independent_unit", ""),
            independent_values=independent_values,
            dependent_var=metadata.get("dependent_var", "종속 변인"),
            dependent_unit=metadata.get("dependent_unit", ""),
            measurements=measurements,
            repetitions=repetitions,
            min_scale=metadata.get("min_scale", 0.01),
            source_file=source_file,
        )

    def _extract_metadata(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """메타데이터 추출"""
        metadata = {"data_start_row": 1}

        # 첫 번째 행에서 메타데이터 추출 시도
        if rows and rows[0]:
            first_row = rows[0]

            # 키-값 쌍 형식 감지 (예: "실험명: 자유낙하")
            for cell in first_row:
                if cell and isinstance(cell, str) and ":" in cell:
                    key, value = cell.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()

                    if "실험" in key and "명" in key:
                        metadata["experiment_name"] = value
                    elif "조작" in key:
                        metadata["independent_var"] = value
                    elif "종속" in key:
                        metadata["dependent_var"] = value
                    elif "단위" in key:
                        if "조작" in key:
                            metadata["independent_unit"] = value
                        else:
                            metadata["dependent_unit"] = value
                    elif "최소" in key and "눈금" in key:
                        metadata["min_scale"] = float(value)

            # 메타데이터가 발견되면 데이터 시작 행 증가
            if len(metadata) > 1:
                metadata["data_start_row"] = 2

        return metadata

    def _detect_repetitions(self, header_row: List[Any]) -> int:
        """헤더에서 반복 횟수 감지"""
        count = 0
        for cell in header_row[1:]:  # 첫 열(조작변인) 제외
            if cell is None or cell == "":
                break
            cell_str = str(cell).lower()
            # "1회", "2회", "측정1", "trial1" 등의 패턴 감지
            if re.match(r"^\d+회?$|^측정\d+$|^trial\s*\d+$|^\d+$", cell_str):
                count += 1
            elif "평균" in cell_str or "average" in cell_str:
                break
            elif "불확도" in cell_str or "uncertainty" in cell_str:
                break
            else:
                count += 1

        return max(count, 3)  # 최소 3회

    def _parse_value(self, value: Any) -> Union[float, str]:
        """값 파싱 (숫자 또는 문자열)"""
        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(value)
        except (ValueError, TypeError):
            return str(value)

    def parse_interactive(
        self,
        experiment_name: str,
        independent_var: str,
        independent_unit: str,
        dependent_var: str,
        dependent_unit: str,
        independent_values: List[Union[float, str]],
        measurements: List[List[float]],
        repetitions: int = 5,
        min_scale: float = 0.01,
        description: Optional[str] = None,
    ) -> ExperimentData:
        """대화형 입력으로 실험 데이터 생성"""
        return ExperimentData(
            experiment_name=experiment_name,
            independent_var=independent_var,
            independent_unit=independent_unit,
            independent_values=independent_values,
            dependent_var=dependent_var,
            dependent_unit=dependent_unit,
            measurements=measurements,
            repetitions=repetitions,
            min_scale=min_scale,
            description=description,
        )

    def parse_text_input(self, text: str) -> Tuple[List[Union[float, str]], List[List[float]]]:
        """텍스트 형식 데이터 파싱

        형식 예시:
        10: 1.43, 1.45, 1.42, 1.44, 1.43
        20: 2.01, 2.03, 2.00, 2.02, 2.01
        30: 2.45, 2.47, 2.44, 2.46, 2.45
        """
        lines = text.strip().split("\n")
        independent_values = []
        measurements = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # "값: 측정1, 측정2, ..." 형식
            if ":" in line:
                ind_part, meas_part = line.split(":", 1)
                ind_value = self._parse_value(ind_part.strip())
                meas_values = [float(v.strip()) for v in meas_part.split(",")]
            # "값 측정1 측정2 ..." 형식 (공백 구분)
            else:
                parts = line.split()
                ind_value = self._parse_value(parts[0])
                meas_values = [float(v) for v in parts[1:]]

            independent_values.append(ind_value)
            measurements.append(meas_values)

        return independent_values, measurements
