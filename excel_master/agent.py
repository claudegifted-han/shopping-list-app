"""
Excel Master 에이전트 메인 모듈

실험 데이터를 처리하고 스프레드시트, 차트, 분석 보고서를 생성합니다.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .config import config, Config
from .parsers.data_models import ExperimentData
from .parsers.data_parser import DataParser
from .sheets.table_builder import TableBuilder
from .sheets.formula_generator import FormulaGenerator
from .charts.chart_builder import ChartBuilder
from .analysis.statistics import StatisticsCalculator
from .analysis.report_generator import ReportGenerator
from .utils import format_result


class ExcelMasterAgent:
    """Excel Master 에이전트 클래스

    실험 데이터 분석 및 스프레드시트 생성을 위한 통합 인터페이스를 제공합니다.

    사용 예시:
    ```python
    # 방법 1: 대화형 입력
    agent = ExcelMasterAgent()
    agent.set_experiment_info(
        experiment_name="자유낙하 실험",
        independent_var="높이",
        independent_unit="cm",
        dependent_var="낙하 시간",
        dependent_unit="s",
        repetitions=5,
        min_scale=0.01
    )
    agent.add_data(10, [0.45, 0.44, 0.46, 0.45, 0.44])
    agent.add_data(20, [0.64, 0.63, 0.65, 0.64, 0.63])
    result = agent.process()

    # 방법 2: 파일 입력
    agent = ExcelMasterAgent()
    result = agent.process_file("experiment_data.csv")
    ```
    """

    def __init__(self, custom_config: Optional[Config] = None):
        self.config = custom_config or config
        self.parser = DataParser()
        self.experiment_data: Optional[ExperimentData] = None

        # 대화형 입력용 임시 저장소
        self._temp_info: Dict[str, Any] = {}
        self._temp_independent_values: List[Union[float, str]] = []
        self._temp_measurements: List[List[float]] = []

    def set_experiment_info(
        self,
        experiment_name: str,
        independent_var: str,
        independent_unit: str,
        dependent_var: str,
        dependent_unit: str,
        repetitions: int = 5,
        min_scale: float = 0.01,
        description: Optional[str] = None,
    ) -> "ExcelMasterAgent":
        """실험 기본 정보 설정"""
        self._temp_info = {
            "experiment_name": experiment_name,
            "independent_var": independent_var,
            "independent_unit": independent_unit,
            "dependent_var": dependent_var,
            "dependent_unit": dependent_unit,
            "repetitions": repetitions,
            "min_scale": min_scale,
            "description": description,
        }
        return self

    def add_data(
        self,
        independent_value: Union[float, str],
        measurements: List[float]
    ) -> "ExcelMasterAgent":
        """데이터 포인트 추가"""
        self._temp_independent_values.append(independent_value)
        self._temp_measurements.append(measurements)
        return self

    def add_data_from_text(self, text: str) -> "ExcelMasterAgent":
        """텍스트 형식 데이터 추가

        형식:
        10: 0.45, 0.44, 0.46, 0.45, 0.44
        20: 0.64, 0.63, 0.65, 0.64, 0.63
        """
        ind_values, measurements = self.parser.parse_text_input(text)
        self._temp_independent_values.extend(ind_values)
        self._temp_measurements.extend(measurements)
        return self

    def _finalize_data(self) -> ExperimentData:
        """대화형 입력 데이터 최종화"""
        if not self._temp_info:
            raise ValueError("실험 정보가 설정되지 않았습니다. set_experiment_info()를 먼저 호출하세요.")

        if not self._temp_measurements:
            raise ValueError("측정 데이터가 없습니다. add_data()로 데이터를 추가하세요.")

        return self.parser.parse_interactive(
            experiment_name=self._temp_info["experiment_name"],
            independent_var=self._temp_info["independent_var"],
            independent_unit=self._temp_info["independent_unit"],
            dependent_var=self._temp_info["dependent_var"],
            dependent_unit=self._temp_info["dependent_unit"],
            independent_values=self._temp_independent_values,
            measurements=self._temp_measurements,
            repetitions=self._temp_info.get("repetitions", 5),
            min_scale=self._temp_info.get("min_scale", 0.01),
            description=self._temp_info.get("description"),
        )

    def load_file(self, file_path: str) -> "ExcelMasterAgent":
        """파일에서 데이터 로드"""
        self.experiment_data = self.parser.parse_file(file_path)
        return self

    def process(
        self,
        output_dir: Optional[str] = None,
        create_chart: bool = True,
        create_report: bool = True,
    ) -> Dict[str, Any]:
        """데이터 처리 및 결과 생성

        Args:
            output_dir: 출력 디렉토리 (None이면 현재 디렉토리)
            create_chart: 차트 생성 여부
            create_report: 보고서 생성 여부

        Returns:
            처리 결과 딕셔너리
        """
        # 데이터 확정
        if self.experiment_data is None:
            self.experiment_data = self._finalize_data()

        # 출력 디렉토리 설정
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = Path(".")

        result = {
            "experiment_name": self.experiment_data.experiment_name,
            "data": self.experiment_data.to_dict(),
        }

        # 통계 계산
        stats_calc = StatisticsCalculator(self.experiment_data)
        result["statistics"] = stats_calc.summary()

        # 표 구조 생성
        table_builder = TableBuilder(self.experiment_data)
        result["table_structure"] = table_builder.build_table_structure()
        result["zapier_instructions"] = table_builder.get_zapier_instructions()

        # 차트 생성
        if create_chart:
            chart_builder = ChartBuilder(self.experiment_data)

            chart_filename = f"{self.experiment_data.experiment_name}_chart.png"
            chart_path = output_path / chart_filename

            chart_builder.create_chart(output_path=str(chart_path))
            result["chart_path"] = str(chart_path)
            result["chart_instructions"] = chart_builder.get_google_sheets_chart_instructions()

        # 보고서 생성
        if create_report:
            report_gen = ReportGenerator(self.experiment_data)

            result["report"] = {
                "summary": report_gen.generate_summary_report(),
                "data_table": report_gen.generate_data_table(),
                "json": report_gen.generate_json_report(),
            }

            # 보고서 파일 저장
            report_filename = f"{self.experiment_data.experiment_name}_report.md"
            report_path = output_path / report_filename

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_gen.generate_summary_report())

            result["report_path"] = str(report_path)

        return result

    def process_file(
        self,
        file_path: str,
        output_dir: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """파일 처리 단축 메서드"""
        self.load_file(file_path)
        return self.process(output_dir=output_dir, **kwargs)

    def get_spreadsheet_data(self) -> List[List[Any]]:
        """스프레드시트용 원시 데이터 반환"""
        if self.experiment_data is None:
            self.experiment_data = self._finalize_data()

        table_builder = TableBuilder(self.experiment_data)
        return table_builder.get_raw_data_for_sheets()

    def get_statistics(self) -> Dict[str, Any]:
        """통계 요약 반환"""
        if self.experiment_data is None:
            self.experiment_data = self._finalize_data()

        stats_calc = StatisticsCalculator(self.experiment_data)
        return stats_calc.summary()

    def get_formatted_results(self) -> List[str]:
        """형식화된 결과 목록 반환 (값 ± 불확도 형식)"""
        if self.experiment_data is None:
            self.experiment_data = self._finalize_data()

        stats_calc = StatisticsCalculator(self.experiment_data)
        results = []

        for i, ind_value in enumerate(self.experiment_data.independent_values):
            stats = stats_calc.get_statistics_for_condition(i)
            result_str = format_result(stats["mean"], stats["uncertainty"])
            results.append(f"{ind_value}: {result_str} {self.experiment_data.dependent_unit}")

        return results

    def create_chart(
        self,
        output_path: Optional[str] = None,
        **kwargs
    ) -> Union[str, bytes]:
        """차트만 생성"""
        if self.experiment_data is None:
            self.experiment_data = self._finalize_data()

        chart_builder = ChartBuilder(self.experiment_data)
        return chart_builder.create_chart(output_path=output_path, **kwargs)

    def generate_report(self, format: str = "markdown") -> str:
        """보고서 생성

        Args:
            format: "markdown", "json", 또는 "latex"
        """
        if self.experiment_data is None:
            self.experiment_data = self._finalize_data()

        report_gen = ReportGenerator(self.experiment_data)

        if format == "markdown":
            return report_gen.generate_summary_report()
        elif format == "json":
            import json
            return json.dumps(report_gen.generate_json_report(), ensure_ascii=False, indent=2)
        elif format == "latex":
            return report_gen.generate_latex_table()
        else:
            raise ValueError(f"지원하지 않는 형식: {format}")

    def get_zapier_mcp_instructions(self) -> Dict[str, Any]:
        """Zapier MCP 도구 사용 지침 반환"""
        if self.experiment_data is None:
            self.experiment_data = self._finalize_data()

        table_builder = TableBuilder(self.experiment_data)
        return table_builder.get_zapier_instructions()

    def reset(self) -> "ExcelMasterAgent":
        """에이전트 상태 초기화"""
        self.experiment_data = None
        self._temp_info = {}
        self._temp_independent_values = []
        self._temp_measurements = []
        return self


def create_agent(custom_config: Optional[Config] = None) -> ExcelMasterAgent:
    """에이전트 팩토리 함수"""
    return ExcelMasterAgent(custom_config)


# CLI 사용을 위한 간단한 인터페이스
def quick_analysis(
    experiment_name: str,
    independent_var: str,
    independent_unit: str,
    dependent_var: str,
    dependent_unit: str,
    data_text: str,
    repetitions: int = 5,
    min_scale: float = 0.01,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """빠른 분석 함수

    Args:
        experiment_name: 실험명
        independent_var: 조작 변인명
        independent_unit: 조작 변인 단위
        dependent_var: 종속 변인명
        dependent_unit: 종속 변인 단위
        data_text: 텍스트 형식 데이터
        repetitions: 반복 횟수
        min_scale: 최소 눈금
        output_dir: 출력 디렉토리

    Returns:
        분석 결과
    """
    agent = ExcelMasterAgent()

    agent.set_experiment_info(
        experiment_name=experiment_name,
        independent_var=independent_var,
        independent_unit=independent_unit,
        dependent_var=dependent_var,
        dependent_unit=dependent_unit,
        repetitions=repetitions,
        min_scale=min_scale,
    )

    agent.add_data_from_text(data_text)

    return agent.process(output_dir=output_dir)
