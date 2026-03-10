from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import cm


class ConciliacionPDFGenerator:
    """Generador profesional de reportes de conciliación bancaria en PDF."""

    MARGIN_X = 2.4 * cm
    MARGIN_TOP = 1.7 * cm
    MARGIN_BOTTOM = 1.5 * cm

    PAGE_WIDTH, PAGE_HEIGHT = A4
    CONTENT_WIDTH = PAGE_WIDTH - (2 * MARGIN_X)

    COLORS = {
        "primary": colors.HexColor("#1F3A5F"),
        "secondary": colors.HexColor("#2E86C1"),
        "accent": colors.HexColor("#1E8449"),
        "warning": colors.HexColor("#D68910"),
        "danger": colors.HexColor("#C0392B"),
        "light": colors.HexColor("#F4F6F7"),
        "lighter": colors.HexColor("#FBFCFC"),
        "mid": colors.HexColor("#D5DBDB"),
        "text": colors.HexColor("#1C2833"),
        "muted": colors.HexColor("#5D6D7E"),
        "white": colors.white,
    }

    def __init__(self, output_filename: str = "reporte_conciliacion.pdf"):
        self.output_path = Path(output_filename)
        if not self.output_path.is_absolute():
            self.output_path = Path.cwd() / self.output_path

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.c = canvas.Canvas(str(self.output_path), pagesize=A4)
        self.page_num = 1
        self.summary_df = pd.DataFrame()

        self.fonts = {
            "regular": "Helvetica",
            "bold": "Helvetica-Bold",
            "italic": "Helvetica-Oblique",
        }

    def _get_metric_value(self, summary_df: pd.DataFrame, metric_name: str, default=0):
        if summary_df is None or summary_df.empty:
            return default
        result = summary_df.loc[summary_df["metric"] == metric_name, "value"]
        return result.iloc[0] if not result.empty else default

    def _safe_float(self, value, default=0.0) -> float:
        try:
            return float(value)
        except Exception:
            return default

    def _format_money(self, value) -> str:
        return f"${self._safe_float(value):,.2f}"

    def _format_percent(self, value) -> str:
        return f"{self._safe_float(value):,.2f}%"

    def _draw_header(self, title: str):
        self.c.setFillColor(self.COLORS["primary"])
        self.c.rect(0, self.PAGE_HEIGHT - 28, self.PAGE_WIDTH, 28, fill=1, stroke=0)

        self.c.setFillColor(self.COLORS["white"])
        self.c.setFont(self.fonts["bold"], 12)
        self.c.drawString(self.MARGIN_X, self.PAGE_HEIGHT - 18, title)

        self.c.setFont(self.fonts["regular"], 8.5)
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.c.drawRightString(
            self.PAGE_WIDTH - self.MARGIN_X,
            self.PAGE_HEIGHT - 18,
            f"{fecha_actual} | Página {self.page_num}",
        )

    def _draw_footer(self):
        y = self.MARGIN_BOTTOM - 0.4 * cm
        self.c.setStrokeColor(self.COLORS["mid"])
        self.c.line(self.MARGIN_X, y + 6, self.PAGE_WIDTH - self.MARGIN_X, y + 6)

        self.c.setFillColor(self.COLORS["muted"])
        self.c.setFont(self.fonts["regular"], 8)
        self.c.drawString(
            self.MARGIN_X,
            y - 2,
            "Reporte generado automáticamente - Sistema de Conciliación Bancaria",
        )

    def _draw_section_title(self, title: str, y: float, level: int = 1) -> float:
        size_map = {1: 16, 2: 13, 3: 11}
        color_map = {
            1: self.COLORS["primary"],
            2: self.COLORS["secondary"],
            3: self.COLORS["muted"],
        }

        self.c.setFillColor(color_map[level])
        self.c.setFont(self.fonts["bold"], size_map[level])
        self.c.drawString(self.MARGIN_X, y, title)

        if level == 1:
            self.c.setStrokeColor(self.COLORS["secondary"])
            self.c.setLineWidth(1.2)
            self.c.line(self.MARGIN_X, y - 5, self.MARGIN_X + 125, y - 5)

        return y - (size_map[level] + 12)

    def _draw_metric_card(self, label: str, value: str, x: float, y: float, width: float, color_key: str):
        card_height = 52

        self.c.setFillColor(self.COLORS["lighter"])
        self.c.roundRect(x, y - card_height, width, card_height, 6, fill=1, stroke=0)

        self.c.setFillColor(self.COLORS[color_key])
        self.c.roundRect(x, y - 6, width, 6, 6, fill=1, stroke=0)

        self.c.setFillColor(self.COLORS["muted"])
        self.c.setFont(self.fonts["regular"], 8.5)
        self.c.drawString(x + 10, y - 20, label)

        self.c.setFillColor(self.COLORS["text"])
        self.c.setFont(self.fonts["bold"], 13)
        self.c.drawString(x + 10, y - 38, str(value))

    def _create_summary_cards(self, summary_df: pd.DataFrame, y_position: float) -> float:
        metrics_map = [
            ("total_movimientos_banco", "Movimientos Banco", "primary"),
            ("total_movimientos_libro", "Movimientos Libro", "primary"),
            ("total_matched", "Conciliados", "accent"),
            ("total_review", "En Revisión", "warning"),
            ("total_unmatched_banco", "No Conciliados Banco", "danger"),
            ("total_unmatched_libro", "No Conciliados Libro", "danger"),
            ("porcentaje_match_sobre_banco", "% Conciliación", "accent"),
            ("diferencia_neta_pendiente", "Diferencia Neta", "warning"),
        ]

        cards_per_row = 4
        gap = 8
        card_width = (self.CONTENT_WIDTH - (gap * (cards_per_row - 1))) / cards_per_row

        for i, (metric, label, color_key) in enumerate(metrics_map):
            value = self._get_metric_value(summary_df, metric, 0)

            if "porcentaje" in metric:
                value = self._format_percent(value)
            elif "diferencia" in metric or "monto" in metric:
                value = self._format_money(value)

            row = i // cards_per_row
            col = i % cards_per_row

            x = self.MARGIN_X + col * (card_width + gap)
            y = y_position - row * 64

            self._draw_metric_card(label, value, x, y, card_width, color_key)

        total_rows = ((len(metrics_map) - 1) // cards_per_row) + 1
        return y_position - total_rows * 64 - 16

    def _draw_key_findings(self, y_position: float) -> float:
        y_position = self._draw_section_title("Hallazgos Clave", y_position, 2)

        total_matched = int(self._safe_float(self._get_metric_value(self.summary_df, "total_matched", 0)))
        total_review = int(self._safe_float(self._get_metric_value(self.summary_df, "total_review", 0)))
        total_unmatched_bank = int(self._safe_float(self._get_metric_value(self.summary_df, "total_unmatched_banco", 0)))
        diferencia_neta = self._get_metric_value(self.summary_df, "diferencia_neta_pendiente", 0)
        avg_days = self._get_metric_value(self.summary_df, "promedio_diferencia_dias_matched", 0)

        findings = [
            ("Conciliación automática", f"Se conciliaron {total_matched} transacciones con reglas de monto, fecha y similitud de texto.", "accent"),
            ("Partidas en revisión", f"Existen {total_review} movimientos con coincidencia parcial que requieren validación manual.", "warning"),
            ("Diferencias pendientes", f"Se detectaron {total_unmatched_bank} movimientos no conciliados del banco con diferencia neta de {self._format_money(diferencia_neta)}.", "danger"),
            ("Eficiencia operativa", f"La diferencia promedio de fecha en coincidencias conciliadas es de {self._safe_float(avg_days):.2f} días.", "secondary"),
        ]

        row_height = 30
        title_x = self.MARGIN_X + 20
        desc_x = self.MARGIN_X + 165

        for i, (title, desc, color_key) in enumerate(findings):
            y = y_position - i * row_height

            if i % 2 == 0:
                self.c.setFillColor(self.COLORS["light"])
                self.c.roundRect(self.MARGIN_X, y - 20, self.CONTENT_WIDTH, 22, 4, fill=1, stroke=0)

            self.c.setFillColor(self.COLORS[color_key])
            self.c.circle(self.MARGIN_X + 9, y - 9, 3, fill=1, stroke=0)

            self.c.setFillColor(self.COLORS["text"])
            self.c.setFont(self.fonts["bold"], 9.2)
            self.c.drawString(title_x, y - 5, title)

            self.c.setFillColor(self.COLORS["muted"])
            self.c.setFont(self.fonts["regular"], 8.8)
            self.c.drawString(desc_x, y - 5, desc[:74])

        return y_position - len(findings) * row_height - 10

    def _draw_control_notes(self, y_position: float) -> float:
        y_position = self._draw_section_title("Observaciones de Control Interno", y_position, 2)

        notes = [
            "Estandarizar descripciones bancarias y contables para reducir partidas en revisión.",
            "Priorizar validación manual de transacciones de alto monto o sin referencia clara.",
            "Revisar diferencias recurrentes por desfase de fecha entre banco y libro.",
            "Evaluar reglas adicionales para comisiones, ajustes y duplicados.",
        ]

        box_height = 78
        self.c.setFillColor(self.COLORS["lighter"])
        self.c.roundRect(self.MARGIN_X, y_position - box_height, self.CONTENT_WIDTH, box_height, 6, fill=1, stroke=0)

        self.c.setFillColor(self.COLORS["text"])
        self.c.setFont(self.fonts["regular"], 9.2)

        line_y = y_position - 16
        for note in notes:
            self.c.drawString(self.MARGIN_X + 12, line_y, f"• {note}")
            line_y -= 15

        return y_position - box_height - 8

    def _normalize_table_rows(
        self,
        df: pd.DataFrame,
        mappings: List[Tuple[str, str]],
        max_rows: int = 8,
    ) -> List[List[str]]:
        table_data = [[header for header, _ in mappings]]

        if df is None or df.empty:
            return table_data

        preview = df.head(max_rows).copy()

        for _, row in preview.iterrows():
            row_data = []
            for _, real_col in mappings:
                if real_col not in preview.columns:
                    row_data.append("N/A")
                    continue

                value = row[real_col]

                if "monto" in real_col.lower():
                    value = self._format_money(value)
                elif "fecha" in real_col.lower():
                    value = str(value)[:10]
                elif "score" in real_col.lower():
                    value = f"{self._safe_float(value):.2f}"
                elif "diff" in real_col.lower():
                    value = str(value)
                else:
                    text = str(value)
                    if "descripcion" in real_col.lower():
                        value = text[:26] + "..." if len(text) > 26 else text
                    else:
                        value = text[:34] + "..." if len(text) > 34 else text

                row_data.append(value)
            table_data.append(row_data)

        return table_data

    def _draw_transactions_table(
        self,
        title: str,
        df: pd.DataFrame,
        mappings: List[Tuple[str, str]],
        y_position: float,
        max_rows: int = 8,
    ) -> float:
        y_position = self._draw_section_title(title, y_position, 3)
        y_position -= 14

        if df is None or df.empty:
            self.c.setFillColor(self.COLORS["muted"])
            self.c.setFont(self.fonts["italic"], 9.5)
            self.c.drawString(self.MARGIN_X, y_position, "No hay registros para mostrar.")
            return y_position - 20

        table_data = self._normalize_table_rows(df, mappings, max_rows=max_rows)
        headers = [header for header, _ in mappings]

        if headers == ["Fecha Banco", "Descripción Banco", "Monto Banco", "Score Texto", "Dif. Días"]:
            col_widths = [
                self.CONTENT_WIDTH * 0.18,
                self.CONTENT_WIDTH * 0.34,
                self.CONTENT_WIDTH * 0.20,
                self.CONTENT_WIDTH * 0.16,
                self.CONTENT_WIDTH * 0.12,
            ]
        elif headers == ["Fecha Banco", "Descripción Banco", "Monto Banco"]:
            col_widths = [
                self.CONTENT_WIDTH * 0.20,
                self.CONTENT_WIDTH * 0.48,
                self.CONTENT_WIDTH * 0.32,
            ]
        else:
            num_cols = len(mappings)
            col_widths = [self.CONTENT_WIDTH / num_cols] * num_cols

        table = Table(table_data, colWidths=col_widths)

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.COLORS["primary"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.COLORS["white"]),
            ("FONTNAME", (0, 0), (-1, 0), self.fonts["bold"]),
            ("FONTSIZE", (0, 0), (-1, 0), 8.3),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("BACKGROUND", (0, 1), (-1, -1), self.COLORS["white"]),
            ("TEXTCOLOR", (0, 1), (-1, -1), self.COLORS["text"]),
            ("FONTNAME", (0, 1), (-1, -1), self.fonts["regular"]),
            ("FONTSIZE", (0, 1), (-1, -1), 7.6),
            ("GRID", (0, 0), (-1, -1), 0.35, self.COLORS["mid"]),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [self.COLORS["white"], self.COLORS["light"]]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))

        estimated_height = len(table_data) * 21
        table.wrapOn(self.c, self.MARGIN_X, y_position)
        table.drawOn(self.c, self.MARGIN_X, y_position - estimated_height)

        return y_position - estimated_height - 18

    def _draw_chart(self, chart_path: str, x: float, y: float, width: float, height: float, title: str = ""):
        if chart_path and Path(chart_path).exists():
            self.c.setStrokeColor(self.COLORS["mid"])
            self.c.setLineWidth(0.8)
            self.c.roundRect(x - 5, y - height - 8, width + 10, height + 22, 5, fill=0, stroke=1)

            if title:
                self.c.setFillColor(self.COLORS["muted"])
                self.c.setFont(self.fonts["bold"], 8.5)
                self.c.drawString(x, y + 5, title)

            self.c.drawImage(
                ImageReader(chart_path),
                x,
                y - height,
                width=width,
                height=height,
                preserveAspectRatio=True,
                mask="auto",
            )

    def generate(
        self,
        summary_df: pd.DataFrame,
        chart_paths: Dict[str, str],
        top_review_df: pd.DataFrame,
        top_unmatched_bank_df: pd.DataFrame,
    ) -> str:
        self.summary_df = summary_df if summary_df is not None else pd.DataFrame()

        # Página 1
        self._draw_header("Reporte Ejecutivo de Conciliación Bancaria")

        y = self.PAGE_HEIGHT - self.MARGIN_TOP
        y = self._draw_section_title("Resumen Ejecutivo", y, 1)
        y = self._create_summary_cards(self.summary_df, y)
        y = self._draw_key_findings(y)
        y = self._draw_control_notes(y)

        chart_y = 255
        half_width = (self.CONTENT_WIDTH / 2) - 8

        self._draw_chart(
            chart_paths.get("status_chart"),
            self.MARGIN_X,
            chart_y,
            half_width,
            135,
            "Distribución de Estados",
        )
        self._draw_chart(
            chart_paths.get("amount_chart"),
            self.MARGIN_X + half_width + 16,
            chart_y,
            half_width,
            135,
            "Montos por Estado",
        )

        self._draw_footer()
        self.c.showPage()
        self.page_num += 1

        # Página 2
        self._draw_header("Análisis Detallado de Transacciones")

        y = self.PAGE_HEIGHT - self.MARGIN_TOP
        y = self._draw_section_title("Partidas Pendientes de Análisis", y, 1)
        y -= 14

        review_mappings = [
            ("Fecha Banco", "fecha_banco"),
            ("Descripción Banco", "descripcion_banco"),
            ("Monto Banco", "monto_banco"),
            ("Score Texto", "text_score"),
            ("Dif. Días", "date_diff"),
        ]

        unmatched_mappings = [
            ("Fecha Banco", "fecha_banco"),
            ("Descripción Banco", "descripcion_banco"),
            ("Monto Banco", "monto_banco"),
        ]

        y = self._draw_transactions_table(
            "Transacciones en Revisión",
            top_review_df,
            review_mappings,
            y,
            max_rows=8,
        )

        y -= 22

        y = self._draw_transactions_table(
            "Transacciones No Conciliadas - Banco",
            top_unmatched_bank_df,
            unmatched_mappings,
            y,
            max_rows=8,
        )

        if y < 250:
            self._draw_footer()
            self.c.showPage()
            self.page_num += 1
            self._draw_header("Análisis Detallado (Continuación)")
            y = self.PAGE_HEIGHT - self.MARGIN_TOP

        self._draw_chart(
            chart_paths.get("top_unmatched_bank_chart"),
            self.MARGIN_X,
            y - 10,
            self.CONTENT_WIDTH,
            170,
            "Top Transacciones No Conciliadas por Monto",
        )

        self._draw_footer()
        self.c.save()
        return str(self.output_path)


def export_executive_pdf(
    summary_df: pd.DataFrame,
    chart_paths: dict,
    top_review_df: pd.DataFrame,
    top_unmatched_bank_df: pd.DataFrame,
    output_filename: str = "reporte_conciliacion.pdf",
) -> str:
    generator = ConciliacionPDFGenerator(output_filename)
    return generator.generate(
        summary_df=summary_df,
        chart_paths=chart_paths or {},
        top_review_df=top_review_df,
        top_unmatched_bank_df=top_unmatched_bank_df,
    )