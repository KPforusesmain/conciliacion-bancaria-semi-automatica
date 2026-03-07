import logging
from datetime import datetime
from pathlib import Path

import colorama
import pandas as pd
from colorama import Back, Fore, Style

from cleaning import clean_bank_data, clean_book_data
from excel_export import export_to_excel
from matching import find_matches
from pdf_report import export_executive_pdf
from report_visuals import generate_all_charts
from reporting import build_kpi_tables, build_summary
from utils import DATA_RAW_DIR, OUTPUT_DIR, ensure_directories


colorama.init(autoreset=True)


def setup_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("reconciliation")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


class ReconciliationReport:
    """Clase principal para manejar el proceso de conciliación bancaria."""

    def __init__(
        self,
        bank_file: str,
        book_file: str,
        company_name: str = "Empresa",
        rules: dict | None = None,
    ):
        self.bank_path = DATA_RAW_DIR / bank_file
        self.book_path = DATA_RAW_DIR / book_file
        self.company_name = company_name
        self.reconciliation_date = datetime.now()
        self.rules = rules or {}

        self.output_dir = OUTPUT_DIR / f"conciliacion_{self.reconciliation_date.strftime('%Y%m%d_%H%M%S')}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger = setup_logger(self.output_dir / "reconciliation.log")

        self.bank_df: pd.DataFrame | None = None
        self.book_df: pd.DataFrame | None = None
        self.matched_df: pd.DataFrame | None = None
        self.review_df: pd.DataFrame | None = None
        self.unmatched_bank_df: pd.DataFrame | None = None
        self.unmatched_book_df: pd.DataFrame | None = None
        self.summary_df: pd.DataFrame | None = None

        self.top_review_df: pd.DataFrame | None = None
        self.top_unmatched_bank_df: pd.DataFrame | None = None
        self.top_unmatched_book_df: pd.DataFrame | None = None

        self.chart_paths: dict = {}
        self.report_paths: dict = {}

    def load_data(self) -> bool:
        try:
            self.logger.info(f"{Fore.CYAN}Cargando datos...{Style.RESET_ALL}")

            if not self.bank_path.exists():
                raise FileNotFoundError(f"No se encontró el archivo de banco: {self.bank_path}")

            if not self.book_path.exists():
                raise FileNotFoundError(f"No se encontró el archivo de libro: {self.book_path}")

            self.bank_df = pd.read_csv(self.bank_path)
            self.book_df = pd.read_csv(self.book_path)

            self.logger.info(f"{Fore.GREEN}✓ Datos cargados exitosamente{Style.RESET_ALL}")
            self.logger.info(f"Banco: {len(self.bank_df)} registros")
            self.logger.info(f"Libro: {len(self.book_df)} registros")
            return True

        except Exception as e:
            self.logger.error(f"{Fore.RED}✗ Error cargando datos: {e}{Style.RESET_ALL}")
            return False

    def clean_data(self) -> bool:
        try:
            self.logger.info(f"{Fore.CYAN}Limpiando datos...{Style.RESET_ALL}")

            if self.bank_df is None or self.book_df is None:
                raise ValueError("Los datos no han sido cargados antes de limpiar.")

            self.bank_df = clean_bank_data(self.bank_df)
            self.book_df = clean_book_data(self.book_df)

            self.logger.info(f"{Fore.GREEN}✓ Datos limpios{Style.RESET_ALL}")
            return True

        except Exception as e:
            self.logger.error(f"{Fore.RED}✗ Error limpiando datos: {e}{Style.RESET_ALL}")
            return False

    def perform_matching(self) -> bool:
        try:
            self.logger.info(f"{Fore.CYAN}Iniciando proceso de matching...{Style.RESET_ALL}")

            if self.bank_df is None or self.book_df is None:
                raise ValueError("Los datos no han sido limpiados/cargados antes del matching.")

            self.matched_df, self.review_df, self.unmatched_bank_df, self.unmatched_book_df = find_matches(
                self.bank_df,
                self.book_df,
                self.rules,
            )

            if self.matched_df is None:
                self.matched_df = pd.DataFrame()
            if self.review_df is None:
                self.review_df = pd.DataFrame()
            if self.unmatched_bank_df is None:
                self.unmatched_bank_df = pd.DataFrame()
            if self.unmatched_book_df is None:
                self.unmatched_book_df = pd.DataFrame()

            self.logger.info(f"{Fore.GREEN}✓ Matching completado{Style.RESET_ALL}")
            self._display_matching_summary()
            return True

        except TypeError as e:
            self.logger.error(
                f"{Fore.RED}✗ Error en matching: {e}. "
                f"Tu archivo matching.py probablemente sigue con la firma vieja "
                f"'find_matches(bank_df, book_df)' en lugar de "
                f"'find_matches(bank_df, book_df, rules)'.{Style.RESET_ALL}"
            )
            return False

        except Exception as e:
            self.logger.error(f"{Fore.RED}✗ Error en matching: {e}{Style.RESET_ALL}")
            return False

    def build_reports_data(self) -> bool:
        try:
            self.logger.info(f"{Fore.CYAN}Construyendo resumen y KPIs...{Style.RESET_ALL}")

            if any(
                df is None
                for df in [
                    self.bank_df,
                    self.book_df,
                    self.matched_df,
                    self.review_df,
                    self.unmatched_bank_df,
                    self.unmatched_book_df,
                ]
            ):
                raise ValueError("Faltan datos de conciliación para construir el resumen.")

            self.summary_df = build_summary(
                bank_df=self.bank_df,
                book_df=self.book_df,
                matched_df=self.matched_df,
                review_df=self.review_df,
                unmatched_bank_df=self.unmatched_bank_df,
                unmatched_book_df=self.unmatched_book_df,
            )

            (
                self.top_review_df,
                self.top_unmatched_bank_df,
                self.top_unmatched_book_df,
            ) = build_kpi_tables(
                matched_df=self.matched_df,
                review_df=self.review_df,
                unmatched_bank_df=self.unmatched_bank_df,
                unmatched_book_df=self.unmatched_book_df,
            )

            if self.top_review_df is None:
                self.top_review_df = pd.DataFrame()
            if self.top_unmatched_bank_df is None:
                self.top_unmatched_bank_df = pd.DataFrame()
            if self.top_unmatched_book_df is None:
                self.top_unmatched_book_df = pd.DataFrame()

            self.logger.info(f"{Fore.GREEN}✓ Resumen y KPIs generados{Style.RESET_ALL}")
            return True

        except Exception as e:
            self.logger.error(f"{Fore.RED}✗ Error construyendo resumen/KPIs: {e}{Style.RESET_ALL}")
            return False

    def generate_reports(self) -> bool:
        try:
            self.logger.info(f"{Fore.CYAN}Generando reportes...{Style.RESET_ALL}")

            if self.summary_df is None:
                raise ValueError("No existe summary_df. Ejecuta build_reports_data primero.")

            export_cfg = self.rules.get("export", {})
            generate_charts = export_cfg.get("generate_charts", True)
            generate_pdf = export_cfg.get("generate_pdf", True)
            generate_excel = export_cfg.get("generate_excel", True)

            self.chart_paths = {}

            if generate_charts:
                self.chart_paths = generate_all_charts(self.summary_df, self.unmatched_bank_df)

            if generate_excel:
                excel_path = export_to_excel(
                    summary_df=self.summary_df,
                    matched_df=self.matched_df if self.matched_df is not None else pd.DataFrame(),
                    review_df=self.review_df if self.review_df is not None else pd.DataFrame(),
                    unmatched_bank_df=self.unmatched_bank_df if self.unmatched_bank_df is not None else pd.DataFrame(),
                    unmatched_book_df=self.unmatched_book_df if self.unmatched_book_df is not None else pd.DataFrame(),
                    top_review_df=self.top_review_df if self.top_review_df is not None else pd.DataFrame(),
                    top_unmatched_bank_df=self.top_unmatched_bank_df if self.top_unmatched_bank_df is not None else pd.DataFrame(),
                    top_unmatched_book_df=self.top_unmatched_book_df if self.top_unmatched_book_df is not None else pd.DataFrame(),
                    output_path=self.output_dir / "reporte_conciliacion.xlsx",
                )
                self.report_paths["excel"] = excel_path

            if generate_pdf:
                pdf_path = export_executive_pdf(
                    summary_df=self.summary_df,
                    chart_paths=self.chart_paths,
                    top_review_df=self.top_review_df if self.top_review_df is not None else pd.DataFrame(),
                    top_unmatched_bank_df=self.top_unmatched_bank_df if self.top_unmatched_bank_df is not None else pd.DataFrame(),
                    output_filename=self.output_dir / "reporte_conciliacion.pdf",
                )
                self.report_paths["pdf"] = pdf_path

            self._export_csv_files()

            self.logger.info(f"{Fore.GREEN}✓ Todos los reportes generados exitosamente{Style.RESET_ALL}")
            return True

        except Exception as e:
            self.logger.error(f"{Fore.RED}✗ Error generando reportes: {e}{Style.RESET_ALL}")
            return False

    def _export_csv_files(self) -> None:
        csv_files = {
            "matched.csv": self.matched_df,
            "review.csv": self.review_df,
            "unmatched_banco.csv": self.unmatched_bank_df,
            "unmatched_libro.csv": self.unmatched_book_df,
            "resumen_conciliacion.csv": self.summary_df,
            "top_review.csv": self.top_review_df,
            "top_unmatched_banco.csv": self.top_unmatched_bank_df,
            "top_unmatched_libro.csv": self.top_unmatched_book_df,
        }

        for filename, df in csv_files.items():
            if df is not None and not df.empty:
                df.to_csv(self.output_dir / filename, index=False)

    def _display_matching_summary(self) -> None:
        total_bank = len(self.bank_df) if self.bank_df is not None else 0
        total_book = len(self.book_df) if self.book_df is not None else 0
        total_matched = len(self.matched_df) if self.matched_df is not None else 0
        total_review = len(self.review_df) if self.review_df is not None else 0
        total_unmatched_bank = len(self.unmatched_bank_df) if self.unmatched_bank_df is not None else 0
        total_unmatched_book = len(self.unmatched_book_df) if self.unmatched_book_df is not None else 0

        print(f"\n{Back.BLUE}{Fore.WHITE} RESUMEN DE CONCILIACIÓN {Style.RESET_ALL}")
        print("=" * 50)

        metrics_display = [
            ("Total Banco", total_bank, ""),
            ("Total Libro", total_book, ""),
            ("Conciliados", total_matched, Fore.GREEN),
            ("Revisión", total_review, Fore.YELLOW),
            ("No Conciliados Banco", total_unmatched_bank, Fore.RED),
            ("No Conciliados Libro", total_unmatched_book, Fore.RED),
        ]

        for label, value, color in metrics_display:
            color = color or Fore.WHITE
            print(f"{color}{label:<25}: {value:>10,}{Style.RESET_ALL}")

        if total_bank > 0:
            conciliation_rate = (total_matched / total_bank) * 100
            print(f"\n{Fore.CYAN}Tasa de Conciliación: {conciliation_rate:.2f}%{Style.RESET_ALL}")

    def _get_metric(self, metric_name: str, default=0):
        if self.summary_df is None or self.summary_df.empty:
            return default

        result = self.summary_df.loc[self.summary_df["metric"] == metric_name, "value"]
        return result.iloc[0] if not result.empty else default

    def generate_executive_summary(self) -> str:
        return f"""
{Back.BLUE}{Fore.WHITE} REPORTE EJECUTIVO DE CONCILIACIÓN {Style.RESET_ALL}
{'=' * 60}
Empresa: {self.company_name}
Fecha: {self.reconciliation_date.strftime('%d/%m/%Y %H:%M')}
Período: {self.reconciliation_date.strftime('%B %Y')}

{Fore.CYAN}RESUMEN DE CONCILIACIÓN:{Style.RESET_ALL}
{'─' * 40}
Total transacciones Banco: {self._get_metric('total_movimientos_banco', 0):>15,}
Total transacciones Libro: {self._get_metric('total_movimientos_libro', 0):>15,}
{Fore.GREEN}Conciliadas: {self._get_metric('total_matched', 0):>24,}{Style.RESET_ALL}
{Fore.YELLOW}En revisión: {self._get_metric('total_review', 0):>23,}{Style.RESET_ALL}
{Fore.RED}No conciliadas Banco: {self._get_metric('total_unmatched_banco', 0):>15,}{Style.RESET_ALL}
{Fore.RED}No conciliadas Libro: {self._get_metric('total_unmatched_libro', 0):>15,}{Style.RESET_ALL}

{Fore.CYAN}MONTOS:{Style.RESET_ALL}
{'─' * 40}
Total Banco: ${self._get_metric('monto_total_banco', 0):>22,.2f}
Total Libro: ${self._get_metric('monto_total_libro', 0):>22,.2f}
{Fore.GREEN}Conciliado Banco: ${self._get_metric('monto_matched_banco', 0):>13,.2f}{Style.RESET_ALL}
{Fore.RED}Diferencia neta pendiente: ${self._get_metric('diferencia_neta_pendiente', 0):>8,.2f}{Style.RESET_ALL}

{Fore.CYAN}INDICADORES CLAVE:{Style.RESET_ALL}
{'─' * 40}
Tasa de conciliación: {self._get_metric('porcentaje_match_sobre_banco', 0):>23.2f}%
Tasa de revisión: {self._get_metric('porcentaje_review_sobre_banco', 0):>27.2f}%
Promedio diferencia días: {self._get_metric('promedio_diferencia_dias_matched', 0):>15.2f}
Promedio text score: {self._get_metric('promedio_text_score_matched', 0):>21.2f}
"""

    def run(self) -> bool:
        print(f"\n{Back.GREEN}{Fore.BLACK} INICIANDO PROCESO DE CONCILIACIÓN {Style.RESET_ALL}\n")

        steps = [
            ("Cargando datos", self.load_data),
            ("Limpiando datos", self.clean_data),
            ("Realizando matching", self.perform_matching),
            ("Construyendo resumen/KPIs", self.build_reports_data),
            ("Generando reportes", self.generate_reports),
        ]

        for step_name, step_func in steps:
            print(f"\n{Fore.YELLOW}▶ {step_name}...{Style.RESET_ALL}")
            if not step_func():
                self.logger.error(f"{Fore.RED}Proceso detenido en: {step_name}{Style.RESET_ALL}")
                return False

        print(self.generate_executive_summary())

        print(f"\n{Back.GREEN}{Fore.BLACK} PROCESO COMPLETADO EXITOSAMENTE {Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Archivos generados en:{Style.RESET_ALL}")
        print(f"  {self.output_dir}")

        if "excel" in self.report_paths:
            print(f"  {self.report_paths['excel']}")

        if "pdf" in self.report_paths:
            print(f"  {self.report_paths['pdf']}")

        return True


def main():
    ensure_directories()

    bank_file = "banco_realista.csv"
    book_file = "libro_realista.csv"
    company_name = "Mi Empresa S.A."

    report = ReconciliationReport(
        bank_file=bank_file,
        book_file=book_file,
        company_name=company_name,
        rules={
            "date_tolerance_days": 2,
            "review_date_tolerance_days": 3,
            "match_text_score": 85,
            "review_text_score": 60,
            "amount_tolerance": 0,
            "export": {
                "generate_charts": True,
                "generate_pdf": True,
                "generate_excel": True,
            },
        },
    )

    success = report.run()
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())