import os
import mysql.connector
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

# Create charts folder
os.makedirs("charts", exist_ok=True)


# Connect to MySQL
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "financial_risk_db")
    )


# Main analysis function
def main():

    print("\nStarting Financial Risk Analysis...")

    db = get_db()

    try:
        print("Connected to MySQL successfully!")

        query = """
            SELECT
                t.transaction_id,
                t.account_id,
                t.transaction_datetime,
                t.amount,
                t.transaction_type,
                t.region,
                COALESCE(a.risk_score, 0) AS risk_score
            FROM transactions t
            LEFT JOIN (
                SELECT
                    transaction_id,
                    MAX(risk_score) AS risk_score
                FROM alerts
                GROUP BY transaction_id
            ) a
            ON t.transaction_id = a.transaction_id
        """

        df = pd.read_sql(query, db)

    finally:
        db.close()

    if df.empty:
        print("No transactions found in database.")
        return

    print("\nTransaction records loaded successfully!")

    # Convert data types
    df["amount"] = pd.to_numeric(df["amount"])

    df["risk_score"] = pd.to_numeric(
        df["risk_score"]
    ).fillna(0)

    df["transaction_datetime"] = pd.to_datetime(
        df["transaction_datetime"]
    )

    # Financial summary
    total_transactions = len(df)

    total_amount = df["amount"].sum()

    average_amount = np.mean(df["amount"])

    print("\n========== FINANCIAL SUMMARY ==========")

    print("Total Transactions:", total_transactions)

    print("Total Transaction Amount:", total_amount)

    print("Average Transaction Amount:", average_amount)

    # Transaction type analysis
    print("\n========== TRANSACTION TYPE ANALYSIS ==========")

    print(df.groupby("transaction_type")["amount"].sum())

    # --------------------------------
    # CHART 1: Transaction Distribution
    # --------------------------------

    plt.figure(figsize=(8, 5))

    plt.hist(df["amount"], bins=10)

    plt.title("Transaction Amount Distribution")

    plt.xlabel("Transaction Amount")

    plt.ylabel("Number of Transactions")

    plt.tight_layout()

    plt.savefig("charts/transaction_distribution.png")

    plt.close()

    # --------------------------------
    # CHART 2: Transaction Types
    # --------------------------------

    plt.figure(figsize=(8, 5))

    df.groupby("transaction_type")["amount"].sum().plot(
        kind="bar"
    )

    plt.title("Transactions by Type")

    plt.xlabel("Transaction Type")

    plt.ylabel("Total Amount")

    plt.tight_layout()

    plt.savefig("charts/transaction_types.png")

    plt.close()

    # --------------------------------
    # CHART 3: Risk Distribution
    # --------------------------------

    plt.figure(figsize=(8, 5))

    plt.hist(
        df["risk_score"],
        bins=[0, 30, 50, 101]
    )

    plt.title("Transaction Risk Score Distribution")

    plt.xlabel("Risk Score")

    plt.ylabel("Number of Transactions")

    plt.tight_layout()

    plt.savefig("charts/risk_distribution.png")

    plt.close()

    print("\n========== ANALYSIS COMPLETED ==========")

    print("Charts generated successfully!")

    print("Check your charts folder.")


if __name__ == "__main__":
    main()