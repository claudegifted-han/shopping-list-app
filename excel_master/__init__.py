"""
Excel Master - 실험 데이터 분석 및 스프레드시트 생성 시스템

실험 원데이터를 구글 스프레드시트에 표로 정리하고,
그래프를 그리며 실험 결과를 분석합니다.
"""

from .config import Config
from .parsers.data_models import ExperimentData
from .parsers.data_parser import DataParser
from .sheets.table_builder import TableBuilder
from .sheets.formula_generator import FormulaGenerator
from .charts.chart_builder import ChartBuilder
from .analysis.statistics import StatisticsCalculator
from .analysis.report_generator import ReportGenerator
from .agent import ExcelMasterAgent

__version__ = "1.0.0"
__all__ = [
    "Config",
    "ExperimentData",
    "DataParser",
    "TableBuilder",
    "FormulaGenerator",
    "ChartBuilder",
    "StatisticsCalculator",
    "ReportGenerator",
    "ExcelMasterAgent",
]
