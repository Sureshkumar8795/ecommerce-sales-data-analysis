"""Clean synthetic order lines, export CSV, and load a local SQLite database."""

from __future__ import annotations

import csv
import json
import sqlite3
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw_data.csv"
CLEAN_PATH = PROJECT_ROOT / "data" / "cleaned_data.csv"
DATABASE_PATH = PROJECT_ROOT / "data" / "ecommerce_sales.db"
QUALITY_PATH = PROJECT_ROOT / "reports" / "data_quality_report.json"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "database_setup.sql"

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
VALID_REGIONS = {"North", "South", "East", "West", "Central"}
VALID_PAYMENTS = {"Credit Card", "PayPal", "Digital Wallet", "Bank Transfer", "Gift Card"}
VALID_STATUSES = {"Delivered", "Processing", "Returned", "Cancelled"}


def mode(values: list[str], fallback: str) -> str:
    counts = Counter(value for value in values if value)
    return counts.most_common(1)[0][0] if counts else fallback


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def clean_records(raw: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()
    for row in raw:
        key = tuple((row.get(field) or "").strip() for field in FIELDS)
        if key in seen:
            continue
        seen.add(key)
        unique.append({field: (row.get(field) or "").strip() for field in FIELDS})

    product_rows: dict[str, dict[str, str]] = {}
    product_prices: dict[str, list[float]] = defaultdict(list)
    customer_names: dict[str, list[str]] = defaultdict(list)
    customer_regions: dict[str, list[str]] = defaultdict(list)
    order_payments: dict[str, list[str]] = defaultdict(list)
    order_statuses: dict[str, list[str]] = defaultdict(list)
    for row in unique:
        product_id = row["Product ID"]
        if product_id:
            known_product = product_rows.setdefault(product_id, row)
            for field in ("Product Category", "Product Name"):
                if not known_product.get(field) and row.get(field):
                    known_product[field] = row[field]
            try:
                product_prices[product_id].append(float(row["Unit Price"]))
            except ValueError:
                pass
        if row["Customer ID"]:
            customer_names[row["Customer ID"]].append(row["Customer Name"])
            customer_regions[row["Customer ID"]].append(row["Region"])
        if row["Order ID"]:
            order_payments[row["Order ID"]].append(row["Payment Method"])
            order_statuses[row["Order ID"]].append(row["Order Status"])

    global_price = statistics.median(
        price for prices in product_prices.values() for price in prices
    )
    product_price = {
        product_id: statistics.median(prices) if prices else global_price
        for product_id, prices in product_prices.items()
    }

    result: list[dict[str, Any]] = []
    dropped_invalid_dates = 0
    missing_sales = 0
    sales_mismatches = 0
    missing_profit = 0
    profit_mismatches = 0
    for row in unique:
        try:
            order_date = datetime.strptime(row["Order Date"], "%Y-%m-%d").date().isoformat()
        except ValueError:
            dropped_invalid_dates += 1
            continue
        if not row["Order ID"] or not row["Customer ID"] or not row["Product ID"]:
            continue

        product = product_rows.get(row["Product ID"], {})
        category = (row["Product Category"] or product.get("Product Category") or "").strip().title()
        category_aliases = {
            "Home & Kitchen": "Home & Kitchen",
            "Home And Kitchen": "Home & Kitchen",
        }
        category = category_aliases.get(category, category)
        if category not in MARGINS:
            category = "Uncategorized"
        name = row["Product Name"] or product.get("Product Name") or "Unknown Product"
        customer_id = row["Customer ID"]
        customer_name = row["Customer Name"] or mode(
            customer_names[customer_id], f"Customer {customer_id}"
        )
        region = (row["Region"] or mode(customer_regions[customer_id], "Central")).title()
        if region not in VALID_REGIONS:
            region = "Central"
        payment = (row["Payment Method"] or mode(
            order_payments[row["Order ID"]], "Credit Card"
        )).title()
        payment_aliases = {"Paypal": "PayPal", "Digital Wallet": "Digital Wallet"}
        payment = payment_aliases.get(payment, payment)
        if payment not in VALID_PAYMENTS:
            payment = "Credit Card"
        status = (row["Order Status"] or mode(
            order_statuses[row["Order ID"]], "Delivered"
        )).title()
        if status not in VALID_STATUSES:
            status = "Processing"

        try:
            quantity = int(float(row["Quantity"]))
        except ValueError:
            quantity = 1
        quantity = max(1, quantity)
        try:
            unit_price = float(row["Unit Price"])
            if unit_price <= 0:
                raise ValueError
        except ValueError:
            unit_price = product_price.get(row["Product ID"], global_price)
        try:
            discount = float(row["Discount"])
        except ValueError:
            discount = 0.0
        discount = min(0.80, max(0.0, discount))

        gross = quantity * unit_price
        expected_sales = round(gross * (1 - discount), 2)
        if not row["Total Sales"]:
            missing_sales += 1
        else:
            try:
                sales_mismatches += abs(float(row["Total Sales"]) - expected_sales) > 0.01
            except ValueError:
                sales_mismatches += 1
        expected_profit = round(
            expected_sales - gross * (1 - MARGINS.get(category, 0.30)), 2
        )
        if not row["Profit"]:
            missing_profit += 1
        else:
            try:
                profit_mismatches += abs(float(row["Profit"]) - expected_profit) > 0.02
            except ValueError:
                profit_mismatches += 1

        result.append({
            "Order ID": row["Order ID"],
            "Order Date": order_date,
            "Customer ID": customer_id,
            "Customer Name": customer_name,
            "Product ID": row["Product ID"],
            "Product Category": category,
            "Product Name": name,
            "Quantity": quantity,
            "Unit Price": round(unit_price, 2),
            "Total Sales": expected_sales,
            "Discount": round(discount, 4),
            "Profit": expected_profit,
            "Region": region,
            "Payment Method": payment,
            "Order Status": status,
        })

    sales = [row["Total Sales"] for row in result]
    q1 = percentile(sales, 0.25)
    q3 = percentile(sales, 0.75)
    iqr = q3 - q1
    upper_fence = q3 + 1.5 * iqr
    report: dict[str, Any] = {
        "synthetic_data": True,
        "seed": 20261117,
        "input_rows": len(raw),
        "missing_values_before_cleaning": {
            field: sum(not row.get(field, "").strip() for row in raw)
            for field in FIELDS
        },
        "duplicate_rows_removed": len(raw) - len(unique),
        "invalid_date_rows_removed": dropped_invalid_dates,
        "cleaned_rows": len(result),
        "missing_values_after_cleaning": {
            field: sum(row.get(field) in ("", None) for row in result)
            for field in FIELDS
        },
        "missing_sales_values_recalculated": missing_sales,
        "sales_calculation_mismatches_recalculated": sales_mismatches,
        "missing_profit_values_recalculated": missing_profit,
        "profit_calculation_mismatches_recalculated": profit_mismatches,
        "sales_outlier_method": "1.5 x IQR upper fence; flagged, not removed",
        "sales_outlier_upper_fence": round(upper_fence, 2),
        "sales_outlier_rows": sum(value > upper_fence for value in sales),
        "calculation_rules": {
            "total_sales": "round(quantity * unit_price * (1 - discount), 2)",
            "profit": "round(total_sales - gross_sales * (1 - category_margin), 2)",
            "analysis_status_scope": "Delivered only",
        },
        "margin_assumptions": MARGINS,
    }
    return result, report


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def write_clean_csv(rows: list[dict[str, Any]]) -> None:
    with CLEAN_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def load_database(rows: list[dict[str, Any]]) -> None:
    statements = SCHEMA_PATH.read_text(encoding="utf-8")
    values = [
        (
            row["Order ID"], row["Order Date"], row["Customer ID"], row["Customer Name"],
            row["Product ID"], row["Product Category"], row["Product Name"], row["Quantity"],
            row["Unit Price"], row["Total Sales"], row["Discount"], row["Profit"],
            row["Region"], row["Payment Method"], row["Order Status"],
        )
        for row in rows
    ]
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.executescript(statements)
        connection.executemany(
            """INSERT INTO order_lines (
                order_id, order_date, customer_id, customer_name, product_id,
                product_category, product_name, quantity, unit_price, total_sales,
                discount, profit, region, payment_method, order_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            values,
        )


def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw dataset not found: {RAW_PATH}. Run generate_data.py first.")
    raw = read_csv(RAW_PATH)
    cleaned, quality_report = clean_records(raw)
    write_clean_csv(cleaned)
    load_database(cleaned)
    QUALITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUALITY_PATH.write_text(json.dumps(quality_report, indent=2), encoding="utf-8")
    print(
        f"Cleaned {len(raw):,} raw rows to {len(cleaned):,} rows; "
        f"database: {DATABASE_PATH}"
    )
    print(
        f"Removed {quality_report['duplicate_rows_removed']} duplicates and "
        f"{quality_report['invalid_date_rows_removed']} invalid dates; "
        f"flagged {quality_report['sales_outlier_rows']} sales outliers (not removed)."
    )


if __name__ == "__main__":
    main()
