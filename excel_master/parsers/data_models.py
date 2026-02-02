"""
실험 데이터 모델 정의

ExperimentData 데이터클래스를 정의합니다.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class ExperimentData:
    """실험 데이터를 저장하는 데이터클래스"""

    # 실험 기본 정보
    experiment_name: str                    # 실험명

    # 조작 변인 (독립 변수)
    independent_var: str                    # 조작 변인명
    independent_unit: str                   # 조작 변인 단위
    independent_values: List[Union[float, str]]  # 조작 변인 값들 (수치 또는 범주)

    # 종속 변인 (종속 변수)
    dependent_var: str                      # 종속 변인명
    dependent_unit: str                     # 종속 변인 단위

    # 측정 데이터
    measurements: List[List[float]]         # 반복 측정값 [조작변인별][반복횟수]

    # 측정 설정
    repetitions: int = 5                    # 반복 측정 횟수 (기본 5)
    min_scale: float = 0.01                 # 측정 도구 최소 눈금

    # 데이터 유형
    is_categorical: bool = False            # 범주형 여부

    # 추가 정보
    description: Optional[str] = None       # 실험 설명
    source_file: Optional[str] = None       # 원본 파일 경로

    def __post_init__(self):
        """데이터 유효성 검사"""
        # 조작변인 개수와 측정 데이터 개수 일치 확인
        if len(self.independent_values) != len(self.measurements):
            raise ValueError(
                f"조작변인 개수({len(self.independent_values)})와 "
                f"측정 데이터 개수({len(self.measurements)})가 일치하지 않습니다."
            )

        # 각 측정 데이터의 반복 횟수 확인
        for i, measurement in enumerate(self.measurements):
            if len(measurement) != self.repetitions:
                raise ValueError(
                    f"조작변인 {self.independent_values[i]}의 측정 횟수({len(measurement)})가 "
                    f"설정된 반복 횟수({self.repetitions})와 일치하지 않습니다."
                )

        # 범주형 여부 자동 감지
        if not self.is_categorical:
            self.is_categorical = self._detect_categorical()

    def _detect_categorical(self) -> bool:
        """조작 변인이 범주형인지 자동 감지"""
        for value in self.independent_values:
            if isinstance(value, str):
                try:
                    float(value)
                except ValueError:
                    return True
        return False

    @property
    def num_conditions(self) -> int:
        """조작 변인 조건 수 반환"""
        return len(self.independent_values)

    @property
    def total_measurements(self) -> int:
        """전체 측정 횟수 반환"""
        return self.num_conditions * self.repetitions

    def get_measurements_for_condition(self, index: int) -> List[float]:
        """특정 조작변인 조건의 측정값 반환"""
        if 0 <= index < len(self.measurements):
            return self.measurements[index]
        raise IndexError(f"인덱스 {index}가 범위를 벗어났습니다.")

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "experiment_name": self.experiment_name,
            "independent_var": self.independent_var,
            "independent_unit": self.independent_unit,
            "independent_values": self.independent_values,
            "dependent_var": self.dependent_var,
            "dependent_unit": self.dependent_unit,
            "measurements": self.measurements,
            "repetitions": self.repetitions,
            "min_scale": self.min_scale,
            "is_categorical": self.is_categorical,
            "description": self.description,
            "source_file": self.source_file,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExperimentData":
        """딕셔너리에서 ExperimentData 생성"""
        return cls(
            experiment_name=data["experiment_name"],
            independent_var=data["independent_var"],
            independent_unit=data["independent_unit"],
            independent_values=data["independent_values"],
            dependent_var=data["dependent_var"],
            dependent_unit=data["dependent_unit"],
            measurements=data["measurements"],
            repetitions=data.get("repetitions", 5),
            min_scale=data.get("min_scale", 0.01),
            is_categorical=data.get("is_categorical", False),
            description=data.get("description"),
            source_file=data.get("source_file"),
        )
