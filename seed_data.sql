USE financial_risk_db;

INSERT IGNORE INTO customers (customer_code)
VALUES
    ('CUST001'),
    ('CUST002'),
    ('CUST003');


-- Create the first customer's savings account

INSERT INTO accounts (customer_id, account_type)
SELECT c.customer_id, 'Savings'
FROM customers c
WHERE c.customer_code = 'CUST001'
AND NOT EXISTS (
    SELECT 1
    FROM accounts a
    WHERE a.customer_id = c.customer_id
);


-- Create the second customer's current account

INSERT INTO accounts (customer_id, account_type)
SELECT c.customer_id, 'Current'
FROM customers c
WHERE c.customer_code = 'CUST002'
AND NOT EXISTS (
    SELECT 1
    FROM accounts a
    WHERE a.customer_id = c.customer_id
);


-- Create the third customer's savings account

INSERT INTO accounts (customer_id, account_type)
SELECT c.customer_id, 'Savings'
FROM customers c
WHERE c.customer_code = 'CUST003'
AND NOT EXISTS (
    SELECT 1
    FROM accounts a
    WHERE a.customer_id = c.customer_id
);


-- Insert an ordinary sample transaction

INSERT INTO transactions (
    account_id,
    transaction_datetime,
    amount,
    transaction_type,
    channel,
    region
)
SELECT
    a.account_id,
    '2026-10-21 10:00:00',
    1200.00,
    'DEPOSIT',
    'Branch',
    'Tirupati'
FROM accounts a
JOIN customers c
    ON c.customer_id = a.customer_id
WHERE c.customer_code = 'CUST001'
AND NOT EXISTS (
    SELECT 1
    FROM transactions t
    WHERE t.account_id = a.account_id
      AND t.transaction_datetime = '2026-10-21 10:00:00'
      AND t.amount = 1200.00
);