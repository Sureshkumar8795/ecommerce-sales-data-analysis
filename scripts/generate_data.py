"""Generate a reproducible synthetic e-commerce order-line dataset."""

from __future__ import annotations

import csv
import random
from calendar import monthrange
from datetime import date
from pathlib import Path

SEED = 20261117
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "raw_data.csv"

FIELDS = [
    "Order ID",
    "Order Date",
    "Customer ID",
    "Customer Name",
    "Product ID",
    "Product Category",
    "Product Name",
    "Quantity",
    "Unit Price",
    "Total Sales",
    "Discount",
    "Profit",
    "Region",
    "Payment Method",
    "Order Status",
]

CATEGORY_PRODUCTS = {
    "Electronics": [
        ("EL-001", "Wireless Headphones", 79.99),
        ("EL-002", "Bluetooth Speaker", 54.50),
        ("EL-003", "Smart Watch", 129.00),
        ("EL-004", "USB-C Hub", 39.95),
        ("EL-005", "Portable SSD", 99.00),
        ("EL-006", "Webcam", 69.00),
        ("EL-007", "Mechanical Keyboard", 89.00),
        ("EL-008", "Wireless Mouse", 34.99),
    ],
    "Home & Kitchen": [
        ("HK-001", "Air Fryer", 119.00),
        ("HK-002", "Coffee Grinder", 49.00),
        ("HK-003", "Ceramic Cookware Set", 149.00),
        ("HK-004", "Cotton Sheet Set", 79.00),
        ("HK-005", "Desk Lamp", 42.00),
        ("HK-006", "Storage Organizer", 28.50),
        ("HK-007", "Water Filter Pitcher", 31.00),
        ("HK-008", "Vacuum Cleaner", 189.00),
    ],
    "Clothing": [
        ("CL-001", "Everyday Hoodie", 48.00),
        ("CL-002", "Classic Denim Jeans", 64.00),
        ("CL-003", "Running Jacket", 92.00),
        ("CL-004", "Cotton T-Shirt", 22.00),
        ("CL-005", "Knit Sweater", 58.00),
        ("CL-006", "Trail Sneakers", 88.00),
        ("CL-007", "Canvas Backpack", 46.00),
        ("CL-008", "Wool Scarf", 29.00),
    ],
    "Beauty": [
        ("BE-001", "Daily Moisturizer", 28.00),
        ("BE-002", "Vitamin C Serum", 36.00),
        ("BE-003", "Sunscreen SPF 50", 19.00),
        ("BE-004", "Hair Care Set", 44.00),
        ("BE-005", "Gentle Cleanser", 21.00),
        ("BE-006", "Body Lotion", 17.50),
        ("BE-007", "Face Mask Pack", 24.00),
        ("BE-008", "Makeup Brush Set", 32.00),
    ],
    "Sports": [
        ("SP-001", "Yoga Mat", 38.00),
        ("SP-002", "Insulated Water Bottle", 26.00),
        ("SP-003", "Resistance Band Set", 21.00),
        ("SP-004", "Adjustable Dumbbell", 159.00),
        ("SP-005", "Cycling Helmet", 74.00),
        ("SP-006", "Fitness Tracker", 99.00),
        ("SP-007", "Camping Lantern", 43.00),
        ("SP-008", "Foam Roller", 32.00),
    ],
}

# Gross margin before discount; shared with clean_data.py for validation.
MARGINS = {
    "Electronics": 0.24,
    "Home & Kitchen": 0.32,
    "Clothing": 0.48,
    "Beauty": 0.55,
    "Sports": 0.38,
}

FIRST_NAMES = [
    "Alex", "Avery", "Blake", "Cameron", "Casey", "Dakota", "Elliot", "Emerson",
    "Harper", "Jamie", "Jordan", "Logan", "Morgan", "Parker", "Quinn", "Riley",
    "Robin", "Rowan", "Sam", "Taylor", "Adrian", "Amara", "Bailey", "Charlie",
]
LAST_NAMES = [
    "Anderson", "Bennett", "Brooks", "Carter", "Chen", "Clark", "Diaz", "Evans",
    "Foster", "Garcia", "Gray", "Hughes", "Kim", "Lewis", "Martin", "Patel",
    "Reed", "Rivera", "Shah", "Turner", "Wong", "Young",
]
REGIONS = ["North", "South", "East", "West", "Central"]
PAYMENTS = ["Credit Card", "PayPal", "Digital Wallet", "Bank Transfer", "Gift Card"]
STATUSES = ["Delivered", "Delivered", "Delivered", "Delivered", "Processing", "Returned", "Cancelled"]
MONTH_WEIGHTS = [0.86, 0.83, 0.91, 0.96, 1.02, 0.98, 1.00, 1.04, 1.08, 1.14, 1.32, 1.40]


def random_order_date(rng: random.Random) -> date:
    """Choose a date with gradual year-over-year growth and seasonal peaks."""
    year_weights = {2023: 0.72, 2024: 0.86, 2025: 1.0}
    weighted_months = [
        (year, month, year_weights[year] * MONTH_WEIGHTS[month - 1])
        for year in (2023, 2024, 2025)
        for month in range(1, 13)
    ]
    year, month, _ = rng.choices(
        weighted_months, weights=[item[2] for item in weighted_months], k=1
    )[0]
    return date(year, month, rng.randint(1, monthrange(year, month)[1]))


def build_records(rng: random.Random) -> list[dict[str, str]]:
    customer_count = 2_500
    customer_names = {
        f"CUST-{number:05d}": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        for number in range(1, customer_count + 1)
    }
    customer_weights = [1 / (number ** 0.72) for number in range(1, customer_count + 1)]
    customer_ids = list(customer_names)
    customer_regions = {
        customer_id: rng.choice(REGIONS) for customer_id in customer_ids
    }
    products = [
        (product_id, category, name, price)
        for category, items in CATEGORY_PRODUCTS.items()
        for product_id, name, price in items
    ]
    product_weights = [
        1.0 / (1.0 + index * 0.025) for index in range(len(products))
    ]

    records: list[dict[str, str]] = []
    for order_number in range(1, 6_501):
        order_id = f"ORD-{order_number:06d}"
        customer_id = rng.choices(customer_ids, weights=customer_weights, k=1)[0]
        order_date = random_order_date(rng)
        line_count = rng.choices([1, 2, 3, 4], weights=[0.28, 0.42, 0.23, 0.07], k=1)[0]
        status = rng.choice(STATUSES)
        payment = rng.choices(PAYMENTS, weights=[0.44, 0.23, 0.19, 0.09, 0.05], k=1)[0]
        for _ in range(line_count):
            product_id, category, name, unit_price = rng.choices(
                products, weights=product_weights, k=1
            )[0]
            quantity = rng.choices([1, 2, 3, 4, 5], weights=[0.48, 0.28, 0.14, 0.07, 0.03], k=1)[0]
            discount = rng.choices(
                [0.0, 0.05, 0.10, 0.15, 0.20, 0.25],
                weights=[0.36, 0.20, 0.19, 0.13, 0.08, 0.04],
                k=1,
            )[0]
            gross_sales = quantity * unit_price
            net_sales = round(gross_sales * (1 - discount), 2)
            profit = round(net_sales - gross_sales * (1 - MARGINS[category]), 2)
            records.append({
                "Order ID": order_id,
                "Order Date": order_date.isoformat(),
                "Customer ID": customer_id,
                "Customer Name": customer_names[customer_id],
                "Product ID": product_id,
                "Product Category": category,
                "Product Name": name,
                "Quantity": str(quantity),
                "Unit Price": f"{unit_price:.2f}",
                "Total Sales": f"{net_sales:.2f}",
                "Discount": f"{discount:.2f}",
                "Profit": f"{profit:.2f}",
                "Region": customer_regions[customer_id],
                "Payment Method": payment,
                "Order Status": status,
            })

    # Introduce realistic, documented quality issues for the cleaning exercise.
    missing_fields = {
        "Customer Name": 20,
        "Product Category": 25,
        "Product Name": 20,
        "Region": 30,
        "Payment Method": 20,
        "Total Sales": 18,
        "Profit": 18,
    }
    for field, count in missing_fields.items():
        for index in rng.sample(range(len(records)), count):
            records[index][field] = ""

    for index in rng.sample(range(len(records)), 40):
        records[index]["Product Category"] = records[index]["Product Category"].upper()
    for index in rng.sample(range(len(records)), 8):
        records[index]["Order Date"] = "not-a-date"

    duplicate_count = 50
    records.extend(dict(row) for row in rng.sample(records, duplicate_count))
    rng.shuffle(records)
    return records


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    records = build_records(random.Random(SEED))
    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print(f"Generated {len(records):,} synthetic order-line records: {OUTPUT}")
    print("All names and transactions are fictional; no real customer data is used.")


if __name__ == "__main__":
    main()
