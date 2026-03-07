import pandas as pd


def build_summary(
    bank_df: pd.DataFrame,
    book_df: pd.DataFrame,
    matched_df: pd.DataFrame,
    review_df: pd.DataFrame,
    unmatched_bank_df: pd.DataFrame,
    unmatched_book_df: pd.DataFrame,
) -> pd.DataFrame:
    total_bank = len(bank_df)
    total_book = len(book_df)
    total_matched = len(matched_df)
    total_review = len(review_df)
    total_unmatched_bank = len(unmatched_bank_df)
    total_unmatched_book = len(unmatched_book_df)

    porcentaje_match = round((total_matched / total_bank) * 100, 2) if total_bank else 0
    porcentaje_review = round((total_review / total_bank) * 100, 2) if total_bank else 0
    porcentaje_unmatched_bank = round((total_unmatched_bank / total_bank) * 100, 2) if total_bank else 0

    monto_total_banco = round(bank_df["monto_banco"].sum(), 2) if "monto_banco" in bank_df.columns else 0
    monto_total_libro = round(book_df["monto_libro"].sum(), 2) if "monto_libro" in book_df.columns else 0

    monto_matched_banco = round(matched_df["monto_banco"].sum(), 2) if not matched_df.empty else 0
    monto_matched_libro = round(matched_df["monto_libro"].sum(), 2) if not matched_df.empty else 0

    monto_review_banco = round(review_df["monto_banco"].sum(), 2) if not review_df.empty else 0
    monto_review_libro = round(review_df["monto_libro"].sum(), 2) if not review_df.empty else 0

    monto_unmatched_banco = round(unmatched_bank_df["monto_banco"].sum(), 2) if not unmatched_bank_df.empty else 0
    monto_unmatched_libro = round(unmatched_book_df["monto_libro"].sum(), 2) if not unmatched_book_df.empty else 0

    avg_date_diff = round(matched_df["date_diff"].mean(), 2) if not matched_df.empty and "date_diff" in matched_df.columns else 0
    avg_text_score = round(matched_df["text_score"].mean(), 2) if not matched_df.empty and "text_score" in matched_df.columns else 0

    max_unmatched_banco = round(unmatched_bank_df["monto_banco"].abs().max(), 2) if not unmatched_bank_df.empty else 0
    max_unmatched_libro = round(unmatched_book_df["monto_libro"].abs().max(), 2) if not unmatched_book_df.empty else 0

    difference_net = round(monto_unmatched_banco - monto_unmatched_libro, 2)

    summary = pd.DataFrame([
        {"metric": "total_movimientos_banco", "value": total_bank},
        {"metric": "total_movimientos_libro", "value": total_book},
        {"metric": "total_matched", "value": total_matched},
        {"metric": "total_review", "value": total_review},
        {"metric": "total_unmatched_banco", "value": total_unmatched_bank},
        {"metric": "total_unmatched_libro", "value": total_unmatched_book},
        {"metric": "porcentaje_match_sobre_banco", "value": porcentaje_match},
        {"metric": "porcentaje_review_sobre_banco", "value": porcentaje_review},
        {"metric": "porcentaje_unmatched_banco", "value": porcentaje_unmatched_bank},
        {"metric": "monto_total_banco", "value": monto_total_banco},
        {"metric": "monto_total_libro", "value": monto_total_libro},
        {"metric": "monto_matched_banco", "value": monto_matched_banco},
        {"metric": "monto_matched_libro", "value": monto_matched_libro},
        {"metric": "monto_review_banco", "value": monto_review_banco},
        {"metric": "monto_review_libro", "value": monto_review_libro},
        {"metric": "monto_unmatched_banco", "value": monto_unmatched_banco},
        {"metric": "monto_unmatched_libro", "value": monto_unmatched_libro},
        {"metric": "diferencia_neta_pendiente", "value": difference_net},
        {"metric": "promedio_diferencia_dias_matched", "value": avg_date_diff},
        {"metric": "promedio_text_score_matched", "value": avg_text_score},
        {"metric": "mayor_unmatched_banco_absoluto", "value": max_unmatched_banco},
        {"metric": "mayor_unmatched_libro_absoluto", "value": max_unmatched_libro},
    ])

    return summary


def build_kpi_tables(
    matched_df: pd.DataFrame,
    review_df: pd.DataFrame,
    unmatched_bank_df: pd.DataFrame,
    unmatched_book_df: pd.DataFrame,
):
    top_review = pd.DataFrame()
    top_unmatched_bank = pd.DataFrame()
    top_unmatched_book = pd.DataFrame()

    if not review_df.empty:
        top_review = review_df.sort_values(
            by=["monto_banco", "text_score"],
            ascending=[False, True]
        ).head(10).copy()

    if not unmatched_bank_df.empty:
        top_unmatched_bank = unmatched_bank_df.copy()
        top_unmatched_bank["abs_monto"] = top_unmatched_bank["monto_banco"].abs()
        top_unmatched_bank = top_unmatched_bank.sort_values(by="abs_monto", ascending=False).head(10)

    if not unmatched_book_df.empty:
        top_unmatched_book = unmatched_book_df.copy()
        top_unmatched_book["abs_monto"] = top_unmatched_book["monto_libro"].abs()
        top_unmatched_book = top_unmatched_book.sort_values(by="abs_monto", ascending=False).head(10)

    return top_review, top_unmatched_bank, top_unmatched_book