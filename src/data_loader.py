"""Loaders for the Olist Brazilian e-commerce CSV files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd


DATASET_FILES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}

STRING_COLUMNS = {
    "customers": ["customer_zip_code_prefix"],
    "sellers": ["seller_zip_code_prefix"],
    "geolocation": ["geolocation_zip_code_prefix"],
}


def _candidate_dirs(data_dir: str | Path | None = None) -> Iterable[Path]:
    if data_dir is not None:
        yield Path(data_dir)

    env_dir = os.getenv("OLIST_DATA_DIR")
    if env_dir:
        yield Path(env_dir)

    project_root = Path(__file__).resolve().parents[1]
    yield project_root / "data"
    yield project_root / "data" / "olist"
    yield project_root / "input"
    yield project_root


def resolve_data_dir(data_dir: str | Path | None = None) -> Path:
    """Return the directory containing the Olist CSV files."""

    orders_file = DATASET_FILES["orders"]
    checked: list[Path] = []

    for candidate in _candidate_dirs(data_dir):
        candidate = candidate.expanduser().resolve()
        checked.append(candidate)
        if (candidate / orders_file).exists():
            return candidate

    project_root = Path(__file__).resolve().parents[1]
    for search_root in (project_root / "data", project_root / "input"):
        if not search_root.exists():
            continue
        for path in search_root.rglob(orders_file):
            if path.is_file():
                return path.parent

    checked_text = "\n".join(f"- {path}" for path in checked)
    raise FileNotFoundError(
        "Could not find the Olist CSV files. Place the extracted Kaggle CSVs "
        "in the data/ directory, or set OLIST_DATA_DIR to their folder.\n"
        f"Checked:\n{checked_text}"
    )


def load_table(table_name: str, data_dir: str | Path | None = None) -> pd.DataFrame:
    """Load one Olist table by logical name."""

    if table_name not in DATASET_FILES:
        valid = ", ".join(sorted(DATASET_FILES))
        raise KeyError(f"Unknown table '{table_name}'. Valid tables: {valid}")

    root = resolve_data_dir(data_dir)
    path = root / DATASET_FILES[table_name]
    if not path.exists():
        raise FileNotFoundError(f"Missing expected dataset file: {path}")

    kwargs = {}
    date_columns = DATE_COLUMNS.get(table_name)
    if date_columns:
        kwargs["parse_dates"] = date_columns

    string_columns = STRING_COLUMNS.get(table_name)
    if string_columns:
        kwargs["dtype"] = {column: "string" for column in string_columns}

    return pd.read_csv(path, **kwargs)


def load_all_data(data_dir: str | Path | None = None) -> Dict[str, pd.DataFrame]:
    """Load all Olist tables into a dictionary of DataFrames."""

    return {name: load_table(name, data_dir=data_dir) for name in DATASET_FILES}
