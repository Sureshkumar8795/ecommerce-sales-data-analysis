"""Calculate data-backed KPIs, business insights, and customer segments."""

from __future__ import annotations

import csv
import sqlite3
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "cleaned_data.csv"
DATABASE_PATH = PROJECT_ROOT / "data" / "ecommerce_sales.db"
REPORT_PATH = PROJECT_ROOT / "reports" / "business_insights.md"


def money(value: float) -> str:
    return f"${value:,.2f}"


def percent(value: float) -> str:
    return f"{value:.1%}"


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Cleaned data not found: {DATA_PATH}. Run clean_data.py first.")
    with DATA_PATH.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    delivered = [row for row in rows if row["Order Status"] == "Delivered"]
    if not delivered:
        raise ValueError("No delivered rows are available for the analysis.")

    revenue = sum(float(row["Total Sales"]) for row in delivered)
    profit = sum(float(row["Profit"]) for row in delivered)
    order_totals: dict[str, float] = defaultdict(float)
    customer_totals: dict[str, float] = defaultdict(float)
    customer_names: dict[str, str] = {}
    category_revenue: dict[str, float] = defaultdict(float)
    category_profit: dict[str, float] = defaultdict(float)
    region_revenue: dict[str, float] = defaultdict(float)
    product_revenue: dict[str, float] = defaultdict(float)
    product_units: dict[str, int] = defaultdict(int)
    monthly_revenue: dict[str, float] = defaultdict(float)
    customer_orders: dict[str, set[str]] = defaultdict(set)
    for row in delivered:
        sales = float(row["Total Sales"])
        row_profit = float(row["Profit"])
        order_id = row["Order ID"]
        customer_id = row["Customer ID"]
        product = row["Product Name"]
        month = row["Order Date"][:7]
        order_totals[order_id] += sales
        customer_totals[customer_id] += sales
        customer_names[customer_id] = row["Customer Name"]
        category_revenue[row["Product Category"]] += sales
        category_profit[row["Product Category"]] += row_profit
        region_revenue[row["Region"]] += sales
        product_revenue[product] += sales
        product_units[product] += int(row["Quantity"])
        monthly_revenue[month] += sales
        customer_orders[customer_id].add(order_id)

    order_count = len(order_totals)
    customer_count = len(customer_totals)
    aov = revenue / order_count
    margin = profit / revenue if revenue else 0
    top_category, top_category_sales = max(category_revenue.items(), key=lambda item: item[1])
    top_region, top_region_sales = max(region_revenue.items(), key=lambda item: item[1])
    top_product, top_product_sales = max(product_revenue.items(), key=lambda item: item[1])
    weakest_margin_category = min(
        category_profit, key=lambda category: category_profit[category] / category_revenue[category]
    )
    monthly = sorted(monthly_revenue.items())
    monthly_growth = [
        (month, (amount / monthly[index - 1][1] - 1) if monthly[index - 1][1] else 0)
        for index, (month, amount) in enumerate(monthly)
        if index > 0
    ]
    best_growth = max(monthly_growth, key=lambda item: item[1])
    worst_growth = min(monthly_growth, key=lambda item: item[1])
    annual_revenue: dict[str, float] = defaultdict(float)
    for month, amount in monthly:
        annual_revenue[month[:4]] += amount
    annual = sorted(annual_revenue.items())
    annual_growth = (
        annual[-1][1] / annual[-2][1] - 1 if len(annual) > 1 and annual[-2][1] else 0
    )
    discount_buckets: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for row in delivered:
        discount = float(row["Discount"])
        label = "0%" if discount == 0 else ("1-10%" if discount <= 0.10 else ("11-20%" if discount <= 0.20 else "21%+"))
        discount_buckets[label].append((float(row["Total Sales"]), float(row["Profit"])))
    discount_stats = {
        label: (
            sum(profit_value for _, profit_value in values) / sum(sales for sales, _ in values),
            len(values),
        )
        for label, values in discount_buckets.items()
    }
    max_date = max(date.fromisoformat(row["Order Date"]) for row in delivered)
    segment_revenue: Counter[str] = Counter()
    segment_customers: Counter[str] = Counter()
    recency_by_customer: dict[str, date] = {}
    for row in delivered:
        customer_id = row["Customer ID"]
        order_date = date.fromisoformat(row["Order Date"])
        recency_by_customer[customer_id] = max(
            recency_by_customer.get(customer_id, date.min), order_date
        )
    for customer_id, value in customer_totals.items():
        frequency = len(customer_orders[customer_id])
        recency = (max_date - recency_by_customer[customer_id]).days
        segment = (
            "Champions" if frequency >= 5 and recency <= 90
            else "Loyal" if frequency >= 3
            else "At Risk" if recency > 180
            else "New / Occasional"
        )
        segment_revenue[segment] += value
        segment_customers[segment] += 1

    top_customer_id, top_customer_spend = max(customer_totals.items(), key=lambda item: item[1])
    top_customer_name = customer_names[top_customer_id]
    repeat_customers = sum(len(order_ids) > 1 for order_ids in customer_orders.values())
    return_rate = sum(row["Order Status"] == "Returned" for row in rows) / len(rows)
    cancel_rate = sum(row["Order Status"] == "Cancelled" for row in rows) / len(rows)

    insights = [
        f"Delivered sales totaled **{money(revenue)}** across **{order_count:,} orders**; average order value was **{money(aov)}**.",
        f"Delivered profit was **{money(profit)}**, for an overall profit margin of **{percent(margin)}**.",
        f"**{top_category}** led category revenue at **{money(top_category_sales)}** ({percent(top_category_sales / revenue)} of delivered sales).",
        f"**{top_region}** was the highest-revenue region at **{money(top_region_sales)}** ({percent(top_region_sales / revenue)} of delivered sales).",
        f"**{top_product}** was the top product by revenue at **{money(top_product_sales)}**; it sold {product_units[top_product]:,} units.",
        f"**{top_customer_name}** was the top customer by delivered spend at **{money(top_customer_spend)}**.",
        f"**{weakest_margin_category}** had the lowest category profit margin at **{percent(category_profit[weakest_margin_category] / category_revenue[weakest_margin_category])}**.",
        f"The highest month-over-month revenue increase was **{best_growth[0]}** at **{percent(best_growth[1])}**.",
        f"The largest month-over-month revenue decline was **{worst_growth[0]}** at **{percent(worst_growth[1])}**.",
        f"Revenue changed **{percent(annual_growth)}** from {annual[-2][0] if len(annual) > 1 else 'the prior year'} to {annual[-1][0]} (delivered orders only).",
        f"**{repeat_customers:,} of {customer_count:,} customers ({percent(repeat_customers / customer_count)})** placed more than one delivered order.",
        f"The largest customer segment by count was **{segment_customers.most_common(1)[0][0]}** ({segment_customers.most_common(1)[0][1]:,} customers).",
        f"Returned and cancelled records represented **{percent(return_rate)}** and **{percent(cancel_rate)}** of cleaned order lines; these statuses are excluded from sales KPIs.",
    ]
    report_lines = [
        "# Business Insights",
        "",
        "> Generated from the cleaned, synthetic dataset. Sales KPIs include delivered order lines only. Values are calculated by `scripts/run_analysis.py`; refresh by rerunning the pipeline.",
        "",
        "## KPI snapshot",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Delivered revenue | {money(revenue)} |",
        f"| Delivered profit | {money(profit)} |",
        f"| Profit margin | {percent(margin)} |",
        f"| Delivered orders | {order_count:,} |",
        f"| Unique delivered customers | {customer_count:,} |",
        f"| Average order value | {money(aov)} |",
        "",
        "## Calculated findings",
        "",
    ]
    report_lines.extend(f"{number}. {insight}" for number, insight in enumerate(insights, start=1))
    report_lines.extend([
        "",
        "## Category performance",
        "",
        "| Category | Revenue | Profit | Margin |",
        "|---|---:|---:|---:|",
    ])
    for category in sorted(category_revenue, key=category_revenue.get, reverse=True):
        report_lines.append(
            f"| {category} | {money(category_revenue[category])} | "
            f"{money(category_profit[category])} | "
            f"{percent(category_profit[category] / category_revenue[category])} |"
        )
    report_lines.extend([
        "",
        "## Customer segments",
        "",
        "| Segment | Customers | Revenue |",
        "|---|---:|---:|",
    ])
    for segment, count in segment_customers.most_common():
        report_lines.append(f"| {segment} | {count:,} | {money(segment_revenue[segment])} |")
    report_lines.extend([
        "",
        "Segment rules: Champions = at least 5 delivered orders and purchased in the last 90 days; Loyal = at least 3 delivered orders; At Risk = no delivered order in over 180 days; otherwise New / Occasional. Recency is measured from the latest delivered order date in this synthetic dataset.",
        "",
        "## Discount profitability",
        "",
        "| Discount band | Order lines | Profit margin |",
        "|---|---:|---:|",
    ])
    for label in ("0%", "1-10%", "11-20%", "21%+"):
        if label in discount_stats:
            band_margin, count = discount_stats[label]
            report_lines.append(f"| {label} | {count:,} | {percent(band_margin)} |")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    with sqlite3.connect(DATABASE_PATH) as connection:
        sql_summary = connection.execute(
            """SELECT COUNT(DISTINCT order_id), COUNT(DISTINCT customer_id),
                      ROUND(SUM(total_sales), 2)
               FROM order_lines WHERE order_status = 'Delivered'"""
        ).fetchone()
    if sql_summary != (order_count, customer_count, round(revenue, 2)):
        raise AssertionError(f"SQLite/Python KPI mismatch: {sql_summary}")
    print(f"Delivered revenue: {money(revenue)} | profit: {money(profit)} | AOV: {money(aov)}")
    print(f"Wrote {len(insights)} data-derived insights to {REPORT_PATH}")


if __name__ == "__main__":
    main()
