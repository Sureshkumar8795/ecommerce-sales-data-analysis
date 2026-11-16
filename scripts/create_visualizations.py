"""Create a presentation-ready EDA dashboard from cleaned CSV data."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "cleaned_data.csv"
OUTPUT_PATH = PROJECT_ROOT / "visualizations" / "sales_dashboard.png"


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Cleaned data not found: {DATA_PATH}. Run clean_data.py first.")
    data = pd.read_csv(DATA_PATH, parse_dates=["Order Date"])
    data = data.loc[data["Order Status"].eq("Delivered")].copy()
    if data.empty:
        raise ValueError("No delivered rows are available for visualization.")
    sns.set_theme(style="whitegrid", context="notebook", palette="deep")
    data["Month"] = data["Order Date"].dt.to_period("M").astype(str)

    monthly = data.groupby("Month", as_index=False)["Total Sales"].sum()
    categories = data.groupby("Product Category", as_index=False).agg(
        Revenue=("Total Sales", "sum"), Profit=("Profit", "sum")
    ).sort_values("Revenue")
    regions = data.groupby("Region", as_index=False)["Total Sales"].sum().sort_values("Total Sales")
    products = (
        data.groupby("Product Name", as_index=False)["Total Sales"]
        .sum()
        .nlargest(10, "Total Sales")
        .sort_values("Total Sales")
    )
    payments = data.groupby("Payment Method", as_index=False)["Total Sales"].sum().sort_values("Total Sales")
    data["Discount Band"] = pd.cut(
        data["Discount"],
        bins=[-0.001, 0, 0.10, 0.20, 0.80],
        labels=["0%", "1-10%", "11-20%", "21%+"],
        include_lowest=True,
    )
    discount_margin = data.groupby("Discount Band", observed=False).agg(
        Profit=("Profit", "sum"), Revenue=("Total Sales", "sum")
    )
    discount_margin["Profit Margin"] = discount_margin["Profit"] / discount_margin["Revenue"]
    customer = data.groupby("Customer ID", as_index=False).agg(
        Spend=("Total Sales", "sum"),
        Orders=("Order ID", "nunique"),
        Last_Order=("Order Date", "max"),
    )
    customer["Recency"] = (data["Order Date"].max() - customer["Last_Order"]).dt.days
    customer["Segment"] = "New / Occasional"
    customer.loc[customer["Recency"].gt(180), "Segment"] = "At Risk"
    customer.loc[customer["Orders"].ge(3), "Segment"] = "Loyal"
    customer.loc[customer["Orders"].ge(5) & customer["Recency"].le(90), "Segment"] = "Champions"
    segment_counts = customer["Segment"].value_counts().sort_values()

    fig, axes = plt.subplots(4, 2, figsize=(18, 22))
    fig.suptitle("E-Commerce Sales Analysis | Delivered Orders", fontsize=22, fontweight="bold", y=0.995)

    sns.lineplot(data=monthly, x="Month", y="Total Sales", marker="o", ax=axes[0, 0], color="#176B87")
    axes[0, 0].set_title("Monthly Revenue Trend")
    axes[0, 0].set_xlabel("")
    axes[0, 0].tick_params(axis="x", rotation=55)
    axes[0, 0].set_ylabel("Revenue ($)")

    sns.barplot(data=categories, x="Revenue", y="Product Category", ax=axes[0, 1], color="#64CCC5")
    axes[0, 1].set_title("Revenue by Category")
    axes[0, 1].set_xlabel("Revenue ($)")
    axes[0, 1].set_ylabel("")

    sns.barplot(data=regions, x="Total Sales", y="Region", ax=axes[1, 0], color="#DAA520")
    axes[1, 0].set_title("Regional Revenue")
    axes[1, 0].set_xlabel("Revenue ($)")
    axes[1, 0].set_ylabel("")

    sns.barplot(data=products, x="Total Sales", y="Product Name", ax=axes[1, 1], color="#4C78A8")
    axes[1, 1].set_title("Top 10 Products by Revenue")
    axes[1, 1].set_xlabel("Revenue ($)")
    axes[1, 1].set_ylabel("")

    sns.scatterplot(
        data=categories, x="Revenue", y="Profit", hue="Product Category",
        s=140, ax=axes[2, 0], legend=False,
    )
    for _, row in categories.iterrows():
        axes[2, 0].annotate(row["Product Category"], (row["Revenue"], row["Profit"]), fontsize=8)
    axes[2, 0].set_title("Category Profit vs Revenue")
    axes[2, 0].set_xlabel("Revenue ($)")
    axes[2, 0].set_ylabel("Profit ($)")

    sns.barplot(data=payments, x="Total Sales", y="Payment Method", ax=axes[2, 1], color="#9B59B6")
    axes[2, 1].set_title("Revenue by Payment Method")
    axes[2, 1].set_xlabel("Revenue ($)")
    axes[2, 1].set_ylabel("")

    axes[3, 0].bar(segment_counts.index, segment_counts.values, color=sns.color_palette("deep", len(segment_counts)))
    axes[3, 0].set_title("Customer Segmentation (Delivered Orders)")
    axes[3, 0].set_ylabel("Unique Customers")
    axes[3, 0].tick_params(axis="x", rotation=20)

    axes[3, 1].bar(
        discount_margin.index.astype(str),
        discount_margin["Profit Margin"].values,
        color="#E07A5F",
    )
    axes[3, 1].set_title("Profit Margin by Discount Band")
    axes[3, 1].set_xlabel("Discount")
    axes[3, 1].set_ylabel("Profit Margin")
    axes[3, 1].yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.0%}"))

    for axis in axes.flat:
        axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved dashboard chart: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
