-- Every revenue/profit KPI below uses completed (Delivered) order lines.

-- 1. Revenue by month.
SELECT substr(order_date, 1, 7) AS sales_month,
       ROUND(SUM(total_sales), 2) AS revenue
FROM order_lines
WHERE order_status = 'Delivered'
GROUP BY sales_month
ORDER BY sales_month;

-- 2. Top 10 products by delivered revenue.
SELECT product_id, product_name, ROUND(SUM(total_sales), 2) AS revenue
FROM order_lines
WHERE order_status = 'Delivered'
GROUP BY product_id, product_name
ORDER BY revenue DESC
LIMIT 10;

-- 3. Top 10 customers by delivered spend.
SELECT customer_id, customer_name, ROUND(SUM(total_sales), 2) AS spend,
       COUNT(DISTINCT order_id) AS delivered_orders
FROM order_lines
WHERE order_status = 'Delivered'
GROUP BY customer_id, customer_name
ORDER BY spend DESC
LIMIT 10;

-- 4. Delivered sales by region.
SELECT region, ROUND(SUM(total_sales), 2) AS revenue,
       ROUND(SUM(profit), 2) AS profit
FROM order_lines
WHERE order_status = 'Delivered'
GROUP BY region
ORDER BY revenue DESC;

-- 5. Category-wise delivered profit and margin.
SELECT product_category, ROUND(SUM(total_sales), 2) AS revenue,
       ROUND(SUM(profit), 2) AS profit,
       ROUND(100.0 * SUM(profit) / NULLIF(SUM(total_sales), 0), 2) AS profit_margin_pct
FROM order_lines
WHERE order_status = 'Delivered'
GROUP BY product_category
ORDER BY profit DESC;

-- 6. Month-over-month revenue and growth percentage (SQLite window function).
WITH monthly AS (
    SELECT substr(order_date, 1, 7) AS sales_month, SUM(total_sales) AS revenue
    FROM order_lines
    WHERE order_status = 'Delivered'
    GROUP BY sales_month
)
SELECT sales_month, ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY sales_month))
             / NULLIF(LAG(revenue) OVER (ORDER BY sales_month), 0), 2) AS mom_growth_pct
FROM monthly
ORDER BY sales_month;

-- 7. Average order value: aggregate lines to distinct orders before averaging.
WITH order_totals AS (
    SELECT order_id, SUM(total_sales) AS order_revenue
    FROM order_lines
    WHERE order_status = 'Delivered'
    GROUP BY order_id
)
SELECT ROUND(AVG(order_revenue), 2) AS average_order_value,
       ROUND(SUM(order_revenue), 2) AS total_revenue,
       COUNT(*) AS delivered_orders
FROM order_totals;

-- 8. Running total of monthly delivered sales.
WITH monthly AS (
    SELECT substr(order_date, 1, 7) AS sales_month, SUM(total_sales) AS revenue
    FROM order_lines
    WHERE order_status = 'Delivered'
    GROUP BY sales_month
)
SELECT sales_month, ROUND(revenue, 2) AS monthly_revenue,
       ROUND(SUM(revenue) OVER (ORDER BY sales_month
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue
FROM monthly
ORDER BY sales_month;

-- 9. Product revenue ranking within category.
WITH product_sales AS (
    SELECT product_category, product_id, product_name, SUM(total_sales) AS revenue
    FROM order_lines
    WHERE order_status = 'Delivered'
    GROUP BY product_category, product_id, product_name
)
SELECT product_category, product_id, product_name,
       ROUND(revenue, 2) AS revenue,
       RANK() OVER (PARTITION BY product_category ORDER BY revenue DESC) AS category_rank
FROM product_sales
ORDER BY product_category, category_rank;

-- 10. Customer segmentation using delivered order recency, frequency, and spend.
WITH customer_rfm AS (
    SELECT customer_id, customer_name,
           MAX(order_date) AS last_order_date,
           COUNT(DISTINCT order_id) AS order_frequency,
           SUM(total_sales) AS monetary_value
    FROM order_lines
    WHERE order_status = 'Delivered'
    GROUP BY customer_id, customer_name
),
scored AS (
    SELECT *,
           CAST(julianday((SELECT MAX(order_date) FROM order_lines
                           WHERE order_status = 'Delivered'))
                - julianday(last_order_date) AS INTEGER) AS recency_days
    FROM customer_rfm
)
SELECT customer_id, customer_name, recency_days, order_frequency,
       ROUND(monetary_value, 2) AS monetary_value,
       CASE
           WHEN order_frequency >= 5 AND recency_days <= 90 THEN 'Champions'
           WHEN order_frequency >= 3 THEN 'Loyal'
           WHEN recency_days > 180 THEN 'At Risk'
           ELSE 'New / Occasional'
       END AS customer_segment
FROM scored
ORDER BY monetary_value DESC;

-- 11. Revenue by payment method for the dashboard.
SELECT payment_method, ROUND(SUM(total_sales), 2) AS revenue,
       COUNT(DISTINCT order_id) AS delivered_orders
FROM order_lines
WHERE order_status = 'Delivered'
GROUP BY payment_method
ORDER BY revenue DESC;
