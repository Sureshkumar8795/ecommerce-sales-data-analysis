-- SQLite schema for cleaned synthetic e-commerce order-line data.
-- Re-running the setup intentionally replaces the existing table.
DROP TABLE IF EXISTS order_lines;

CREATE TABLE order_lines (
    line_id INTEGER PRIMARY KEY,
    order_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    product_id TEXT NOT NULL,
    product_category TEXT NOT NULL,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    total_sales REAL NOT NULL,
    discount REAL NOT NULL CHECK (discount >= 0 AND discount <= 0.8),
    profit REAL NOT NULL,
    region TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    order_status TEXT NOT NULL
);

CREATE INDEX idx_order_lines_date ON order_lines(order_date);
CREATE INDEX idx_order_lines_customer ON order_lines(customer_id);
CREATE INDEX idx_order_lines_product ON order_lines(product_id);
CREATE INDEX idx_order_lines_status ON order_lines(order_status);
