import pandas as pd
from rapidfuzz import fuzz


def calculate_date_diff_days(date_a, date_b) -> int:
    """Calcula diferencia absoluta en días entre dos fechas."""
    if pd.isna(date_a) or pd.isna(date_b):
        return 999999
    return abs((date_a - date_b).days)


def text_similarity(text_a: str, text_b: str) -> int:
    """Calcula similitud de texto usando token_sort_ratio."""
    text_a = "" if pd.isna(text_a) else str(text_a)
    text_b = "" if pd.isna(text_b) else str(text_b)
    return fuzz.token_sort_ratio(text_a, text_b)


def validate_required_columns(bank_df: pd.DataFrame, book_df: pd.DataFrame) -> None:
    """Valida que existan las columnas necesarias."""
    required_bank_cols = {
        "fecha_banco",
        "descripcion_banco",
        "descripcion_banco_norm",
        "monto_banco",
        "matched_flag",
    }
    required_book_cols = {
        "fecha_libro",
        "descripcion_libro",
        "descripcion_libro_norm",
        "monto_libro",
        "matched_flag",
    }

    missing_bank = required_bank_cols - set(bank_df.columns)
    missing_book = required_book_cols - set(book_df.columns)

    if missing_bank:
        raise ValueError(f"Faltan columnas requeridas en bank_df: {sorted(missing_bank)}")

    if missing_book:
        raise ValueError(f"Faltan columnas requeridas en book_df: {sorted(missing_book)}")


def get_rules(rules: dict) -> dict:
    """Obtiene reglas con valores por defecto."""
    return {
        "date_tolerance_days": rules.get("date_tolerance_days", 2),
        "review_date_tolerance_days": rules.get("review_date_tolerance_days", 3),
        "match_text_score": rules.get("match_text_score", 85),
        "review_text_score": rules.get("review_text_score", 60),
        "amount_tolerance": rules.get("amount_tolerance", 0),
    }


def amount_matches(book_amount: float, bank_amount: float, amount_tolerance: float = 0) -> bool:
    """Evalúa coincidencia por monto con tolerancia opcional."""
    if pd.isna(book_amount) or pd.isna(bank_amount):
        return False
    return abs(book_amount - bank_amount) <= amount_tolerance


def build_match_record(
    bank_idx,
    book_idx,
    bank_row,
    book_row,
    date_diff: int,
    text_score: int,
    status: str,
) -> dict:
    """Construye el registro de salida para matched/review."""
    return {
        "bank_index": bank_idx,
        "book_index": book_idx,
        "fecha_banco": bank_row["fecha_banco"],
        "descripcion_banco": bank_row["descripcion_banco"],
        "monto_banco": bank_row["monto_banco"],
        "fecha_libro": book_row["fecha_libro"],
        "descripcion_libro": book_row["descripcion_libro"],
        "monto_libro": book_row["monto_libro"],
        "date_diff": date_diff,
        "text_score": text_score,
        "status": status,
    }


def find_matches(bank_df: pd.DataFrame, book_df: pd.DataFrame, rules: dict):
    """
    Realiza conciliación entre movimientos bancarios y libro contable.

    Retorna:
        matched_df, review_df, unmatched_bank_df, unmatched_book_df
    """
    validate_required_columns(bank_df, book_df)

    # Trabajar sobre copias para evitar efectos secundarios fuera de la función
    bank_df = bank_df.copy()
    book_df = book_df.copy()

    cfg = get_rules(rules)

    date_tolerance_days = cfg["date_tolerance_days"]
    review_date_tolerance_days = cfg["review_date_tolerance_days"]
    match_text_score = cfg["match_text_score"]
    review_text_score = cfg["review_text_score"]
    amount_tolerance = cfg["amount_tolerance"]

    matched_rows = []
    review_rows = []

    bank_available = bank_df[~bank_df["matched_flag"]]

    for bank_idx, bank_row in bank_available.iterrows():
        candidates = book_df[~book_df["matched_flag"]].copy()

        if candidates.empty:
            continue

        # Filtrar por monto primero
        candidates = candidates[
            candidates["monto_libro"].apply(
                lambda x: amount_matches(x, bank_row["monto_banco"], amount_tolerance)
            )
        ].copy()

        if candidates.empty:
            continue

        # Calcular score por fecha y texto
        candidates["date_diff"] = candidates["fecha_libro"].apply(
            lambda x: calculate_date_diff_days(bank_row["fecha_banco"], x)
        )
        candidates["text_score"] = candidates["descripcion_libro_norm"].apply(
            lambda x: text_similarity(bank_row["descripcion_banco_norm"], x)
        )

        # MATCH exacto/fuerte
        exact_candidates = candidates[
            (candidates["date_diff"] <= date_tolerance_days) &
            (candidates["text_score"] >= match_text_score)
        ].sort_values(by=["date_diff", "text_score"], ascending=[True, False])

        if not exact_candidates.empty:
            best = exact_candidates.iloc[0]
            book_idx = best.name

            bank_df.at[bank_idx, "matched_flag"] = True
            book_df.at[book_idx, "matched_flag"] = True

            matched_rows.append(
                build_match_record(
                    bank_idx=bank_idx,
                    book_idx=book_idx,
                    bank_row=bank_row,
                    book_row=best,
                    date_diff=int(best["date_diff"]),
                    text_score=int(best["text_score"]),
                    status="matched",
                )
            )
            continue

        # MATCH probable para revisión
        review_candidates = candidates[
            (candidates["date_diff"] <= review_date_tolerance_days) &
            (candidates["text_score"] >= review_text_score)
        ].sort_values(by=["date_diff", "text_score"], ascending=[True, False])

        if not review_candidates.empty:
            best = review_candidates.iloc[0]

            review_rows.append(
                build_match_record(
                    bank_idx=bank_idx,
                    book_idx=best.name,
                    bank_row=bank_row,
                    book_row=best,
                    date_diff=int(best["date_diff"]),
                    text_score=int(best["text_score"]),
                    status="review",
                )
            )

    matched_df = pd.DataFrame(matched_rows)
    review_df = pd.DataFrame(review_rows)

    unmatched_bank_df = bank_df[~bank_df["matched_flag"]].copy()
    unmatched_book_df = book_df[~book_df["matched_flag"]].copy()

    return matched_df, review_df, unmatched_bank_df, unmatched_book_df