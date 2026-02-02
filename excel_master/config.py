"""
Excel Master 설정 모듈

t-값, 기본값, 색상 등의 설정을 관리합니다.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Config:
    """Excel Master 설정 클래스"""

    # t-값 테이블 (자유도별, 95% 신뢰수준)
    T_VALUES: Dict[int, float] = field(default_factory=lambda: {
        2: 4.30,   # 3회 반복 (n-1=2)
        3: 3.18,   # 4회 반복 (n-1=3)
        4: 2.78,   # 5회 반복 (n-1=4)
        5: 2.57,   # 6회 반복
        6: 2.45,   # 7회 반복
        7: 2.36,   # 8회 반복
        8: 2.31,   # 9회 반복
        9: 2.26,   # 10회 반복
        10: 2.23,  # 11회 반복
    })

    # 기본 반복 측정 횟수
    DEFAULT_REPETITIONS: int = 5

    # 기본 t-값 (5회 반복)
    DEFAULT_T_VALUE: float = 2.78

    # 열 레이아웃 설정
    COLUMN_LAYOUT: Dict[str, str] = field(default_factory=lambda: {
        "empty": "A",           # 공백 (변환용 예비)
        "independent": "B",     # 조작 변인
        "measurements_start": "C",  # 반복 측정 시작
        "measurements_end": "G",    # 반복 측정 끝 (5회 기준)
        "average": "H",         # 평균
        "uncertainty": "I",     # 측정 불확도
    })

    # 행 레이아웃 설정
    ROW_LAYOUT: Dict[str, int] = field(default_factory=lambda: {
        "merged_header": 1,     # 병합 헤더 행
        "sub_header": 2,        # 세부 헤더 행
        "data_start": 3,        # 데이터 시작 행
    })

    # 서식 설정
    HEADER_BACKGROUND_COLOR: str = "#FFFFC0"  # 연한 노란색
    HEADER_FONT_WEIGHT: str = "bold"

    # 숫자 형식
    DEFAULT_DECIMAL_PLACES: int = 2

    # 차트 설정
    CHART_TYPES: Dict[str, str] = field(default_factory=lambda: {
        "numerical": "scatter",  # 수치형 → 분산형
        "categorical": "bar",    # 범주형 → 막대형
    })

    # matplotlib 설정
    CHART_FIGURE_SIZE: tuple = (10, 6)
    CHART_DPI: int = 150
    CHART_STYLE: str = "seaborn-v0_8-whitegrid"

    def get_t_value(self, repetitions: int) -> float:
        """반복 횟수에 따른 t-값 반환"""
        df = repetitions - 1  # 자유도
        return self.T_VALUES.get(df, self.DEFAULT_T_VALUE)

    def get_measurement_columns(self, repetitions: int) -> list:
        """반복 횟수에 따른 측정값 열 목록 반환"""
        start_col = ord(self.COLUMN_LAYOUT["measurements_start"])
        return [chr(start_col + i) for i in range(repetitions)]

    def get_average_column(self, repetitions: int) -> str:
        """반복 횟수에 따른 평균 열 반환"""
        start_col = ord(self.COLUMN_LAYOUT["measurements_start"])
        return chr(start_col + repetitions)

    def get_uncertainty_column(self, repetitions: int) -> str:
        """반복 횟수에 따른 불확도 열 반환"""
        start_col = ord(self.COLUMN_LAYOUT["measurements_start"])
        return chr(start_col + repetitions + 1)


# 전역 설정 인스턴스
config = Config()
