"""Run focused checks over the generated CSV, SQLite database, and SQL examples."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "Order ID", "Order Date", "Customer ID", "Customer Name", "Product ID",
    "Product Category", "Product Name", "Quantity", "Unit Price", "Total Sales",
    "Discount", "Profit", "Region", "Payment Method", "Order Status",
]
MARGINS = {
    "Electronics": 0.24,
    "Home & Kitchen": 0.32,
    "Clothing": 0.48,
    "Beauty": 0.55,
    "Sports": 0.38,
}


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def main() -> None:
    raw_path = PROJECT_ROOT / "data" / "raw_data.csv"
    clean_path = PROJECT_ROOT / "data" / "cleaned_data.csv"
    db_path = PROJECT_ROOT / "data" / "ecommerce_sales.db"
    query_path = PROJECT_ROOT / "sql" / "analysis_queries.sql"
    raw_rows = load_rows(raw_path)
    rows = load_rows(clean_path)
    assert len(raw_rows) >= 10_000, f"Raw data has only {len(raw_rows)} rows."
    assert len(rows) >= 10_000, f"Cleaned data has only {len(rows)} rows."
    assert list(rows[0]) == FIELDS, "Cleaned dataset columns do not match the project specification."
    assert len({tuple(row[field] for field in FIELDS) for row in rows}) == len(rows), "Duplicates remain."
    assert all(row["Order Status"] in {"Delivered", "Processing", "Returned", "Cancelled"} for row in rows)
    assert all(float(row["Discount"]) <= 0.8 for row in rows)
    assert all(int(row["Quantity"]) > 0 for row in rows)
    for row in rows:
        gross = int(row["Quantity"]) * float(row["Unit Price"])
        expected_sales = round(gross * (1 - float(row["Discount"])), 2)
        expected_profit = round(
            expected_sales - gross * (1 - MARGINS.get(row["Product Category"], 0.30)), 2
        )
        assert float(row["Total Sales"]) == expected_sales, "Sales calculation is inconsistent."
        assert abs(float(row["Profit"]) - expected_profit) <= 0.01, "Profit calculation is inconsistent."

    with sqlite3.connect(db_path) as connection:
        table_count = connection.execute("SELECT COUNT(*) FROM order_lines").fetchone()[0]
        assert table_count == len(rows), f"Database has {table_count} rows; expected {len(rows)}."
        delivered_csv = [row for row in rows if row["Order Status"] == "Delivered"]
        expected_revenue = round(sum(float(row["Total Sales"]) for row in delivered_csv), 2)
        actual_revenue = connection.execute(
            "SELECT ROUND(SUM(total_sales), 2) FROM order_lines WHERE order_status = 'Delivered'"
        ).fetchone()[0]
        assert actual_revenue == expected_revenue, "CSV and SQLite delivered revenue differ."

        query_text = query_path.read_text(encoding="utf-8")
        sql_without_comments = "\n".join(
            line for line in query_text.splitlines() if not line.lstrip().startswith("--")
        )
        statements = [statement.strip() for statement in sql_without_comments.split(";") if statement.strip()]
        assert len(statements) >= 10, "Expected at least 10 practical SQL queries."
        for number, statement in enumerate(statements, start=1):
            cursor = connection.execute(statement)
            cursor.fetchmany(2)
            assert cursor.description is not None, f"SQL example {number} did not return a result set."

    print(
        f"PASS: {len(raw_rows):,} raw rows, {len(rows):,} unique cleaned rows, "
        f"{table_count:,} database rows, {len(statements)} SQL queries."
    )


if __name__ == "__main__":
    main()
