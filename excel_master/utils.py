"""
유틸리티 모듈

유효숫자 처리, 반올림 등의 공통 유틸리티 함수를 제공합니다.
"""

import math
from typing import Tuple, Union


def count_significant_figures(value: float) -> int:
    """유효숫자 개수 계산"""
    if value == 0:
        return 1

    # 과학적 표기법으로 변환하여 유효숫자 추출
    value_str = f"{abs(value):.15g}"

    # 지수 표기 제거
    if 'e' in value_str.lower():
        mantissa = value_str.lower().split('e')[0]
    else:
        mantissa = value_str

    # 소수점 제거하고 선행 0 제거
    digits = mantissa.replace('.', '').lstrip('0')

    return len(digits) if digits else 1


def get_decimal_places_from_uncertainty(uncertainty: float) -> int:
    """불확도에서 소수점 자릿수 결정

    불확도의 첫 번째 유효숫자 위치에 맞춤

    예시:
    - 불확도 0.05 → 소수점 2자리
    - 불확도 0.3 → 소수점 1자리
    - 불확도 5.2 → 소수점 0자리
    """
    if uncertainty == 0 or uncertainty < 0:
        return 2  # 기본값

    # 불확도의 자릿수 계산
    if uncertainty >= 1:
        return 0
    else:
        # log10으로 자릿수 계산
        decimal_places = -math.floor(math.log10(abs(uncertainty)))
        return max(0, decimal_places)


def round_to_uncertainty(value: float, uncertainty: float) -> Tuple[float, float]:
    """불확도에 맞춰 값 반올림

    규칙:
    1. 불확도를 유효숫자 1자리로 반올림
    2. 측정값을 불확도와 같은 자릿수로 반올림

    Args:
        value: 측정값 (예: 평균)
        uncertainty: 불확도

    Returns:
        (반올림된 값, 반올림된 불확도)
    """
    if uncertainty <= 0:
        return value, 0.0

    # 불확도의 첫 번째 유효숫자 위치 찾기
    if uncertainty >= 1:
        # 1 이상인 경우
        magnitude = math.floor(math.log10(uncertainty))
        round_to = -magnitude
    else:
        # 1 미만인 경우
        magnitude = math.floor(math.log10(uncertainty))
        round_to = -magnitude

    # 불확도 반올림 (유효숫자 1자리)
    rounded_uncertainty = round(uncertainty, round_to)

    # 측정값도 같은 자릿수로 반올림
    rounded_value = round(value, round_to)

    return rounded_value, rounded_uncertainty


def format_with_uncertainty(
    value: float,
    uncertainty: float,
    include_plus_minus: bool = False
) -> Tuple[str, str]:
    """불확도에 맞춘 형식화된 문자열 반환

    Args:
        value: 측정값
        uncertainty: 불확도
        include_plus_minus: ± 기호 포함 여부

    Returns:
        (형식화된 값, 형식화된 불확도)
    """
    rounded_value, rounded_uncertainty = round_to_uncertainty(value, uncertainty)

    # 소수점 자릿수 결정
    decimal_places = get_decimal_places_from_uncertainty(uncertainty)

    # 형식화
    value_str = f"{rounded_value:.{decimal_places}f}"
    uncertainty_str = f"{rounded_uncertainty:.{decimal_places}f}"

    if include_plus_minus:
        return value_str, f"±{uncertainty_str}"

    return value_str, uncertainty_str


def format_result(value: float, uncertainty: float) -> str:
    """결과를 "값 ± 불확도" 형식으로 반환"""
    value_str, uncertainty_str = format_with_uncertainty(value, uncertainty)
    return f"{value_str} ± {uncertainty_str}"


def parse_number(value: Union[str, float, int]) -> float:
    """다양한 형식의 숫자 파싱"""
    if isinstance(value, (int, float)):
        return float(value)

    # 문자열 정리
    value_str = str(value).strip()

    # 천단위 구분자 제거
    value_str = value_str.replace(',', '')

    # 한글 숫자 단위 처리
    korean_units = {
        '만': 10000,
        '억': 100000000,
        '조': 1000000000000,
    }

    for unit, multiplier in korean_units.items():
        if unit in value_str:
            parts = value_str.split(unit)
            if len(parts) == 2:
                base = float(parts[0]) if parts[0] else 0
                remainder = float(parts[1]) if parts[1] else 0
                return base * multiplier + remainder

    return float(value_str)


def format_scientific(value: float, precision: int = 3) -> str:
    """과학적 표기법으로 형식화"""
    if value == 0:
        return "0"

    return f"{value:.{precision}e}"


def get_order_of_magnitude(value: float) -> int:
    """자릿수(지수) 반환"""
    if value == 0:
        return 0
    return math.floor(math.log10(abs(value)))


def normalize_unit(unit: str) -> str:
    """단위 정규화"""
    unit_map = {
        's': 's',
        'sec': 's',
        '초': 's',
        'm': 'm',
        'cm': 'cm',
        'mm': 'mm',
        '미터': 'm',
        '센티미터': 'cm',
        '밀리미터': 'mm',
        'kg': 'kg',
        'g': 'g',
        '킬로그램': 'kg',
        '그램': 'g',
    }

    return unit_map.get(unit.lower().strip(), unit)


def validate_measurements(measurements: list) -> Tuple[bool, str]:
    """측정값 유효성 검사"""
    if not measurements:
        return False, "측정값이 없습니다."

    for i, m in enumerate(measurements):
        if not isinstance(m, (int, float)):
            return False, f"측정값 {i+1}이 숫자가 아닙니다: {m}"

        if math.isnan(m) or math.isinf(m):
            return False, f"측정값 {i+1}이 유효하지 않습니다: {m}"

    return True, "유효합니다."


def detect_outliers_iqr(values: list, multiplier: float = 1.5) -> list:
    """IQR 방법으로 이상치 탐지

    Args:
        values: 측정값 리스트
        multiplier: IQR 배수 (기본 1.5)

    Returns:
        이상치 인덱스 리스트
    """
    if len(values) < 4:
        return []

    sorted_values = sorted(values)
    n = len(sorted_values)

    q1 = sorted_values[n // 4]
    q3 = sorted_values[3 * n // 4]
    iqr = q3 - q1

    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr

    outliers = []
    for i, v in enumerate(values):
        if v < lower_bound or v > upper_bound:
            outliers.append(i)

    return outliers


def interpolate_linear(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """선형 보간"""
    if x2 == x1:
        return y1

    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)
