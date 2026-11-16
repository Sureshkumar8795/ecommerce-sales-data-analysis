# E-Commerce Sales Analysis & Business Intelligence Dashboard

An end-to-end, resume-ready data analytics project that generates clearly labeled synthetic sales transactions, cleans and validates them, loads SQLite, analyzes business performance, creates charts, and documents a Power BI dashboard build.

> **Data notice:** The included data is synthetic and for demonstration only. It is not real customer data. Profit depends on explicit, assumed category margins; it is not accounting data.

## Business problem

An e-commerce team needs a repeatable view of sales, profitability, product/category mix, customer purchasing behavior, regional performance, discount impact, and monthly changes. This project demonstrates a reproducible workflow from raw data through analysis and dashboard-ready outputs.

## Objectives

- Build a deterministic dataset with more than 10,000 transaction lines and realistic data-quality issues.
- Clean, standardize, validate, and export a reusable analysis table.
- Persist the cleaned data in SQLite and answer practical business questions with SQL.
- Calculate KPIs, customer segments, and at least 10 data-derived findings.
- Produce an EDA notebook and a multi-chart dashboard image.
- Provide Power BI measures and implementation guidance.

## Technologies

Python 3.10+, Pandas, NumPy, Matplotlib, Seaborn, Jupyter, SQLite, SQL, and Power BI Desktop (optional, Microsoft application).

## Project structure

```text
ecommerce-sales-analysis/
├── data/
│   ├── README.md
│   ├── raw_data.csv                 # generated synthetic source data
│   ├── cleaned_data.csv             # standardized order-line data
│   └── ecommerce_sales.db           # SQLite database
├── notebooks/
│   ├── data_cleaning.ipynb
│   └── exploratory_data_analysis.ipynb
├── sql/
│   ├── analysis_queries.sql
│   └── database_setup.sql
├── scripts/
│   ├── generate_data.py
│   ├── clean_data.py
│   ├── run_analysis.py
│   ├── create_visualizations.py
│   └── validate_project.py
├── visualizations/                  # generated chart outputs
├── dashboard/
│   └── powerbi_instructions.md
├── reports/
│   ├── business_insights.md
│   └── data_quality_report.json
└── requirements.txt
```

## Dataset

Each CSV row is an order line (an order may have multiple products). The specified fields include order/customer/product identifiers and names, date, category, quantity, unit price, line sales, discount, profit, region, payment method, and status. The generator is deterministic (seed `20261117`) and spans 2023-2025.

| Field | Definition |
|---|---|
| Total Sales | `quantity * unit_price * (1 - discount)`, rounded to cents |
| Profit | Net sales less modeled product cost, based on the category margin assumptions in `scripts/generate_data.py` |
| Order Status | Delivered, Processing, Returned, or Cancelled |

Business revenue and profit KPIs use delivered lines only; returned/cancelled values are not subtracted as refunds. See [data/README.md](data/README.md) for provenance and assumptions.

## Setup

From the project directory in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use the interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the complete pipeline

Run these commands from `ecommerce-sales-analysis/`:

```powershell
.\.venv\Scripts\python.exe scripts\generate_data.py
.\.venv\Scripts\python.exe scripts\clean_data.py
.\.venv\Scripts\python.exe scripts\run_analysis.py
.\.venv\Scripts\python.exe scripts\create_visualizations.py
.\.venv\Scripts\python.exe scripts\validate_project.py
```

The generator is deterministic. Cleaning removes exact duplicates and invalid dates, fills missing descriptive fields using product/customer/order context, standardizes categories and payment/status labels, checks/recalculates sales and profit, and flags (rather than deletes) 1.5 x IQR high-sales outliers. The SQLite database is rebuilt from the cleaned CSV.

## SQL analysis

Open `data/ecommerce_sales.db` using any SQLite client or Python's built-in `sqlite3`. Queries in `sql/analysis_queries.sql` cover monthly revenue and growth, top products/customers, region/category performance, AOV at the order grain, running totals, window-function ranking, customer RFM segmentation, and payment method mix. `scripts/validate_project.py` executes each query against the database.

## Notebooks and charts

Open `notebooks/data_cleaning.ipynb` and `notebooks/exploratory_data_analysis.ipynb` in Jupyter or VS Code. Charts are generated into `visualizations/sales_dashboard.png` using Matplotlib and Seaborn after dependencies are installed.

## Power BI

Follow [dashboard/powerbi_instructions.md](dashboard/powerbi_instructions.md) to import the cleaned CSV, create a date table and delivered-only DAX measures, and assemble KPI cards, trends, category/region/product/customer/payment visuals, and slicers. A `.pbix` is intentionally not claimed as generated because Power BI Desktop is a separate application and is not part of this source pipeline.

## Key findings

Calculated findings are written by `scripts/run_analysis.py` to `reports/business_insights.md`; no metric or business claim is manually invented. That report includes actual dataset KPIs, category margins, sales patterns, discount bands, and customer segments.

## Screenshots

Run `scripts/create_visualizations.py` after installing the requirements to generate `visualizations/sales_dashboard.png`. The Power BI section can be populated with a screenshot after building the report in Power BI Desktop.

## Future improvements

- Replace synthetic data with an approved, privacy-reviewed source and document its business definitions.
- Model actual returns/refunds, shipping costs, taxes, and customer acquisition costs.
- Add automated tests/CI, a star schema, incremental refresh, and forecast evaluation.
- Add Power BI drill-through pages and date-slicer-aware RFM measures.
