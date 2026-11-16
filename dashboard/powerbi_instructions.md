# Power BI Dashboard Build Guide

## 1. Load and model the data

1. Run the Python pipeline and open Power BI Desktop.
2. Select **Get data → Text/CSV** and import `data/cleaned_data.csv`.
3. In Power Query, rename the imported query/table to `order_lines`. Set `Order Date` to **Date**, `Quantity` to **Whole number**, and `Unit Price`, `Total Sales`, `Discount`, and `Profit` to **Decimal number**.
4. Create a date table with **Modeling → New table**:

   ```DAX
   Date = CALENDAR(MIN(order_lines[Order Date]), MAX(order_lines[Order Date]))
   ```

5. Add a year/month label and sort it chronologically:

   ```DAX
   Year Month = FORMAT('Date'[Date], "YYYY-MM")
   Year Month Sort = YEAR('Date'[Date]) * 100 + MONTH('Date'[Date])
   ```

6. Create a one-to-many relationship from `Date[Date]` to `order_lines[Order Date]`, mark `Date` as the date table, and sort `Year Month` by `Year Month Sort`.
7. Keep this dashboard focused on delivered orders. Returned and cancelled order lines stay available for operational analysis but are not recognized revenue in the measures below.

## 2. Create measures

```DAX
Delivered Revenue =
CALCULATE(SUM(order_lines[Total Sales]), order_lines[Order Status] = "Delivered")

Delivered Profit =
CALCULATE(SUM(order_lines[Profit]), order_lines[Order Status] = "Delivered")

Delivered Orders =
CALCULATE(DISTINCTCOUNT(order_lines[Order ID]), order_lines[Order Status] = "Delivered")

Delivered Customers =
CALCULATE(DISTINCTCOUNT(order_lines[Customer ID]), order_lines[Order Status] = "Delivered")

Average Order Value = DIVIDE([Delivered Revenue], [Delivered Orders])

Profit Margin = DIVIDE([Delivered Profit], [Delivered Revenue])

Delivered Units =
CALCULATE(SUM(order_lines[Quantity]), order_lines[Order Status] = "Delivered")
```

For the KPI row use **Card** visuals for Delivered Revenue, Delivered Profit, Delivered Orders, Delivered Customers, and Average Order Value. Format currency to two decimal places and order/customer counts as whole numbers.

## 3. Suggested report layout

- **Top row:** five KPI cards.
- **Middle left:** line chart with `Date[Year Month]` and `[Delivered Revenue]`.
- **Middle right:** clustered bar chart with product category and revenue; use profit as a tooltip.
- **Bottom left:** bar chart of revenue by region.
- **Bottom center:** top 10 product names by revenue (visual-level Top N filter).
- **Bottom right:** revenue by payment method and customer segment.
- Add a scatter chart with category revenue on X and profit on Y to show profit versus revenue.
- Add slicers for `Date[Date]`, `Region`, `Product Category`, and `Payment Method`.
- Add a status slicer only on a separate operational page; the KPI measures intentionally remain delivered-only.

## 4. Customer segment visual

Create a separate customer summary table in Power Query by grouping delivered rows by `Customer ID` and `Customer Name`, aggregating distinct orders, total spend, and latest order date. Add a recency measure/column based on the latest delivered date in the selected dataset, then classify customers using:

- Champions: at least 5 delivered orders and recency at most 90 days.
- Loyal: at least 3 delivered orders.
- At Risk: recency over 180 days.
- New / Occasional: all remaining customers.

These are project-defined RFM rules, not a universal industry standard. For date slicer-specific segments, calculate recency in measures rather than a refresh-time column.

## 5. Design and export

Use a 16:9 canvas, a restrained navy/teal palette, consistent units, readable labels, and descriptive alt text. Avoid 3-D visuals and unnecessary gridlines. Include a subtitle: **“Synthetic demonstration data — not actual customer transactions.”** Save the `.pbix` in `dashboard/` if Power BI Desktop is available. The project includes this build guide rather than a fabricated `.pbix` file.
