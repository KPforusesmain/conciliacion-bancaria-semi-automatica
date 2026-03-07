import random
from datetime import datetime, timedelta

import pandas as pd

from utils import DATA_RAW_DIR, ensure_directories


random.seed(42)


CLIENTES = [
    "CLIENTE ALFA", "CLIENTE BETA", "CLIENTE GAMMA", "CLIENTE DELTA",
    "CLIENTE OMEGA", "CLIENTE NOVA", "CLIENTE SIGMA", "CLIENTE LUNA"
]

PROVEEDORES = [
    "PROVEEDOR XYZ", "PROVEEDOR ABC", "SERVICIOS TECNICOS CR",
    "LOGISTICA CENTRAL", "SUMINISTROS DEL VALLE", "TECNO RED"
]

SERVICIOS = [
    "SERVICIO INTERNET", "SERVICIO ELECTRICO", "SERVICIO AGUA",
    "TELEFONIA CORPORATIVA", "PLATAFORMA SOFTWARE"
]

TEXT_VARIANTS = {
    "TRANSFERENCIA": ["TRANSFERENCIA", "TRANSF", "TRF", "PAGO TRANSFERENCIA"],
    "DEPOSITO": ["DEPOSITO", "DEP", "ABONO", "INGRESO"],
    "PAGO": ["PAGO", "PAGO A", "CANCELACION", "EGRESO"],
    "COMISION": ["COMISION BANCARIA", "CARGO BANCARIO", "COMISION MES"],
    "AJUSTE": ["AJUSTE", "AJUSTE CONTABLE", "REGULARIZACION"]
}


def random_date(start_date: datetime, days_range: int) -> datetime:
    return start_date + timedelta(days=random.randint(0, days_range))


def maybe_shift_date(date_value: datetime, max_shift_days: int = 3) -> datetime:
    shift = random.choice([0, 0, 0, 1, 1, 2, -1, -2, 3])
    shift = max(-max_shift_days, min(max_shift_days, shift))
    return date_value + timedelta(days=shift)


def amount_pool():
    return [
        125000.00, 87500.00, 45200.00, 95000.00, 30000.00, 60000.00,
        45250.00, 18900.00, 1250.00, 5000.00, 250000.00, 77500.00,
        15400.00, 9800.00, 42000.00, 112500.00, 3500.00, 74500.00
    ]


def build_bank_description(mov_type: str, entity: str) -> str:
    variant = random.choice(TEXT_VARIANTS[mov_type])
    return f"{variant} {entity}".strip()


def build_book_description(mov_type: str, entity: str) -> str:
    if mov_type == "TRANSFERENCIA":
        options = [
            f"TRANSF {entity}",
            f"TRANSFERENCIA {entity}",
            f"ABONO {entity}",
            f"INGRESO POR {entity}"
        ]
    elif mov_type == "DEPOSITO":
        options = [
            f"DEPOSITO {entity}",
            f"INGRESO EFECTIVO {entity}",
            f"ABONO {entity}",
            f"DEP {entity}"
        ]
    elif mov_type == "PAGO":
        options = [
            f"PAGO A {entity}",
            f"EGRESO {entity}",
            f"CANCELACION {entity}",
            f"PAGO {entity}"
        ]
    elif mov_type == "COMISION":
        options = [
            "COMISION BANCARIA MES",
            "CARGO BANCARIO",
            "COMISION BANCARIA",
            "GASTO BANCARIO"
        ]
    else:
        options = [
            "AJUSTE CONTABLE",
            "REGULARIZACION",
            "ASIENTO AJUSTE",
            "AJUSTE"
        ]
    return random.choice(options)


def create_base_transactions(num_records: int = 120):
    start_date = datetime(2026, 1, 1)

    bank_rows = []
    book_rows = []

    trx_counter = 1000
    lb_counter = 2000

    for _ in range(num_records):
        movement_class = random.choices(
            population=["TRANSFERENCIA", "DEPOSITO", "PAGO", "COMISION", "AJUSTE"],
            weights=[35, 20, 25, 10, 10],
            k=1
        )[0]

        if movement_class in ["TRANSFERENCIA", "DEPOSITO"]:
            entity = random.choice(CLIENTES)
            amount = random.choice([x for x in amount_pool() if x >= 30000])
            signed_amount = amount
        elif movement_class == "PAGO":
            entity = random.choice(PROVEEDORES + SERVICIOS)
            amount = random.choice(amount_pool())
            signed_amount = -abs(amount)
        elif movement_class == "COMISION":
            entity = ""
            amount = random.choice([1250.00, 2500.00, 3500.00, 9800.00])
            signed_amount = -abs(amount)
        else:
            entity = ""
            amount = random.choice([5000.00, 7500.00, 12000.00])
            signed_amount = random.choice([-abs(amount), abs(amount)])

        bank_date = random_date(start_date, 59)
        book_date = maybe_shift_date(bank_date)

        bank_desc = build_bank_description(movement_class, entity).strip()
        book_desc = build_book_description(movement_class, entity).strip()

        bank_rows.append({
            "fecha_banco": bank_date.strftime("%Y-%m-%d"),
            "descripcion_banco": bank_desc,
            "monto_banco": round(signed_amount, 2),
            "referencia_banco": f"TRX{trx_counter}"
        })

        book_rows.append({
            "fecha_libro": book_date.strftime("%Y-%m-%d"),
            "descripcion_libro": book_desc,
            "monto_libro": round(signed_amount, 2),
            "referencia_libro": f"LB{lb_counter}",
            "cuenta_contable": random.choice(["1101", "2101", "4101", "5202", "5301", "5901"])
        })

        trx_counter += 1
        lb_counter += 1

    return pd.DataFrame(bank_rows), pd.DataFrame(book_rows)


def inject_unmatched(bank_df: pd.DataFrame, book_df: pd.DataFrame):
    extra_bank = pd.DataFrame([
        {
            "fecha_banco": "2026-02-14",
            "descripcion_banco": "TRANSFERENCIA CLIENTE ESPECIAL",
            "monto_banco": 133333.00,
            "referencia_banco": "TRX9991"
        },
        {
            "fecha_banco": "2026-02-18",
            "descripcion_banco": "AJUSTE BANCARIO EXTRAORDINARIO",
            "monto_banco": -22000.00,
            "referencia_banco": "TRX9992"
        }
    ])

    extra_book = pd.DataFrame([
        {
            "fecha_libro": "2026-02-16",
            "descripcion_libro": "ASIENTO MANUAL NO REFLEJADO BANCO",
            "monto_libro": -15000.00,
            "referencia_libro": "LB9991",
            "cuenta_contable": "5901"
        },
        {
            "fecha_libro": "2026-02-20",
            "descripcion_libro": "INGRESO REGISTRADO PENDIENTE BANCO",
            "monto_libro": 88888.00,
            "referencia_libro": "LB9992",
            "cuenta_contable": "4101"
        }
    ])

    bank_df = pd.concat([bank_df, extra_bank], ignore_index=True)
    book_df = pd.concat([book_df, extra_book], ignore_index=True)
    return bank_df, book_df


def inject_review_cases(bank_df: pd.DataFrame, book_df: pd.DataFrame):
    if len(bank_df) >= 10 and len(book_df) >= 10:
        bank_df.loc[3, "descripcion_banco"] = "PAGO PROVEEDOR SERVICIOS TECNICOS"
        book_df.loc[3, "descripcion_libro"] = "EGRESO SERV TEC CR"

        bank_df.loc[7, "descripcion_banco"] = "DEPOSITO CLIENTE NOVA"
        book_df.loc[7, "descripcion_libro"] = "ABONO NOVA"

        bank_df.loc[11, "descripcion_banco"] = "COMISION BANCARIA ENERO"
        book_df.loc[11, "descripcion_libro"] = "GASTO BANCARIO"

    return bank_df, book_df


def generate_realistic_datasets(num_records: int = 120):
    ensure_directories()

    bank_df, book_df = create_base_transactions(num_records=num_records)
    bank_df, book_df = inject_unmatched(bank_df, book_df)
    bank_df, book_df = inject_review_cases(bank_df, book_df)

    bank_path = DATA_RAW_DIR / "banco_realista.csv"
    book_path = DATA_RAW_DIR / "libro_realista.csv"

    bank_df.to_csv(bank_path, index=False)
    book_df.to_csv(book_path, index=False)

    print(f"Datasets generados:")
    print(f"- {bank_path}")
    print(f"- {book_path}")
    print(f"Banco: {len(bank_df)} registros")
    print(f"Libro: {len(book_df)} registros")


if __name__ == "__main__":
    generate_realistic_datasets()