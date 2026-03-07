import matplotlib.pyplot as plt
import pandas as pd

from utils import IMG_DIR, ensure_directories


def save_status_chart(summary_df: pd.DataFrame) -> str:
    ensure_directories()

    def get_metric(name: str):
        value = summary_df.loc[summary_df["metric"] == name, "value"]
        return float(value.iloc[0]) if not value.empty else 0

    labels = ["Matched", "Review", "Unmatched Banco"]
    values = [
        get_metric("total_matched"),
        get_metric("total_review"),
        get_metric("total_unmatched_banco"),
    ]

    plt.figure(figsize=(8, 5))
    plt.bar(labels, values)
    plt.title("Estado de conciliación")
    plt.ylabel("Cantidad de movimientos")
    plt.tight_layout()

    output_path = IMG_DIR / "grafico_estados.png"
    plt.savefig(output_path, dpi=150)
    plt.close()
    return str(output_path)


def save_amount_chart(summary_df: pd.DataFrame) -> str:
    ensure_directories()

    def get_metric(name: str):
        value = summary_df.loc[summary_df["metric"] == name, "value"]
        return float(value.iloc[0]) if not value.empty else 0

    labels = ["Matched", "Review", "Unmatched Banco", "Unmatched Libro"]
    values = [
        abs(get_metric("monto_matched_banco")),
        abs(get_metric("monto_review_banco")),
        abs(get_metric("monto_unmatched_banco")),
        abs(get_metric("monto_unmatched_libro")),
    ]

    plt.figure(figsize=(9, 5))
    plt.bar(labels, values)
    plt.title("Montos por estado")
    plt.ylabel("Monto absoluto")
    plt.tight_layout()

    output_path = IMG_DIR / "grafico_montos.png"
    plt.savefig(output_path, dpi=150)
    plt.close()
    return str(output_path)


def save_top_unmatched_bank_chart(unmatched_bank_df: pd.DataFrame) -> str | None:
    ensure_directories()

    if unmatched_bank_df.empty:
        return None

    chart_df = unmatched_bank_df.copy()
    chart_df["abs_monto"] = chart_df["monto_banco"].abs()
    chart_df = chart_df.sort_values(by="abs_monto", ascending=False).head(10)

    labels = chart_df["descripcion_banco"].astype(str).str.slice(0, 30)
    values = chart_df["abs_monto"]

    plt.figure(figsize=(10, 6))
    plt.barh(labels, values)
    plt.title("Top diferencias no conciliadas - Banco")
    plt.xlabel("Monto absoluto")
    plt.tight_layout()

    output_path = IMG_DIR / "top_diferencias_banco.png"
    plt.savefig(output_path, dpi=150)
    plt.close()
    return str(output_path)


def generate_all_charts(summary_df: pd.DataFrame, unmatched_bank_df: pd.DataFrame) -> dict:
    chart_paths = {
        "status_chart": save_status_chart(summary_df),
        "amount_chart": save_amount_chart(summary_df),
        "top_unmatched_bank_chart": save_top_unmatched_bank_chart(unmatched_bank_df),
    }
    return chart_paths