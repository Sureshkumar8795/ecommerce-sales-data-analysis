# Business Insights

> Generated from the cleaned, synthetic dataset. Sales KPIs include delivered order lines only. Values are calculated by `scripts/run_analysis.py`; refresh by rerunning the pipeline.

## KPI snapshot

| Metric | Value |
|---|---:|
| Delivered revenue | $874,976.95 |
| Delivered profit | $256,998.56 |
| Profit margin | 29.4% |
| Delivered orders | 3,759 |
| Unique delivered customers | 1,484 |
| Average order value | $232.77 |

## Calculated findings

1. Delivered sales totaled **$874,976.95** across **3,759 orders**; average order value was **$232.77**.
2. Delivered profit was **$256,998.56**, for an overall profit margin of **29.4%**.
3. **Electronics** led category revenue at **$276,218.73** (31.6% of delivered sales).
4. **North** was the highest-revenue region at **$203,197.50** (23.2% of delivered sales).
5. **Vacuum Cleaner** was the top product by revenue at **$69,986.70**; it sold 399 units.
6. **Casey Anderson** was the top customer by delivered spend at **$32,266.56**.
7. **Electronics** had the lowest category profit margin at **17.8%**.
8. The highest month-over-month revenue increase was **2025-07** at **57.5%**.
9. The largest month-over-month revenue decline was **2025-01** at **-36.8%**.
10. Revenue changed **6.0%** from 2024 to 2025 (delivered orders only).
11. **745 of 1,484 customers (50.2%)** placed more than one delivered order.
12. The largest customer segment by count was **At Risk** (826 customers).
13. Returned and cancelled records represented **14.2%** and **14.0%** of cleaned order lines; these statuses are excluded from sales KPIs.

## Category performance

| Category | Revenue | Profit | Margin |
|---|---:|---:|---:|
| Electronics | $276,218.73 | $49,059.38 | 17.8% |
| Home & Kitchen | $266,904.81 | $70,737.39 | 26.5% |
| Clothing | $144,697.65 | $63,611.97 | 44.0% |
| Sports | $123,056.95 | $40,795.97 | 33.2% |
| Beauty | $64,098.81 | $32,793.85 | 51.2% |

## Customer segments

| Segment | Customers | Revenue |
|---|---:|---:|
| At Risk | 826 | $249,460.54 |
| New / Occasional | 293 | $100,363.62 |
| Loyal | 279 | $246,549.67 |
| Champions | 86 | $278,603.12 |

Segment rules: Champions = at least 5 delivered orders and purchased in the last 90 days; Loyal = at least 3 delivered orders; At Risk = no delivered order in over 180 days; otherwise New / Occasional. Recency is measured from the latest delivered order date in this synthetic dataset.

## Discount profitability

| Discount band | Order lines | Profit margin |
|---|---:|---:|
| 0% | 2,797 | 34.8% |
| 1-10% | 3,113 | 29.2% |
| 11-20% | 1,612 | 21.7% |
| 21%+ | 323 | 12.4% |
