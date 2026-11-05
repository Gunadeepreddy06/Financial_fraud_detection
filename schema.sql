CREATE DATABASE IF NOT EXISTS financial_risk_db;

USE financial_risk_db;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_code VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    account_type VARCHAR(30) NOT NULL,

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    transaction_datetime DATETIME NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    channel VARCHAR(30) NOT NULL,
    region VARCHAR(60),

    CHECK (amount > 0),

    CHECK (
        transaction_type IN (
            'DEPOSIT',
            'WITHDRAWAL',
            'TRANSFER'
        )
    ),

    FOREIGN KEY (account_id)
        REFERENCES accounts(account_id),

    INDEX idx_transactions_account_datetime (
        account_id,
        transaction_datetime
    )
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    risk_score INT NOT NULL,
    review_status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (risk_score BETWEEN 0 AND 100),

    CHECK (
        review_status IN (
            'Pending',
            'Reviewed',
            'Escalated',
            'Cleared'
        )
    ),

    FOREIGN KEY (transaction_id)
        REFERENCES transactions(transaction_id),

    INDEX idx_alerts_status (review_status)
);