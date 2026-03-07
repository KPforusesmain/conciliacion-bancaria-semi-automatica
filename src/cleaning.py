import pandas as pd


def normalize_text(text: str) -> str:
    if pd.isna(text):
        return ""
    text = str(text).strip().upper()
    replacements = {
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        ",": "",
        ".": "",
        "-": " ",
        "_": " ",
        "/": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = " ".join(text.split())
    return text


def clean_bank_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["fecha_banco"] = pd.to_datetime(df["fecha_banco"], errors="coerce")
    df["monto_banco"] = pd.to_numeric(df["monto_banco"], errors="coerce")
    df["descripcion_banco_norm"] = df["descripcion_banco"].apply(normalize_text)
    df["matched_flag"] = False
    return df


def clean_book_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["fecha_libro"] = pd.to_datetime(df["fecha_libro"], errors="coerce")
    df["monto_libro"] = pd.to_numeric(df["monto_libro"], errors="coerce")
    df["descripcion_libro_norm"] = df["descripcion_libro"].apply(normalize_text)
    df["matched_flag"] = False
    return df