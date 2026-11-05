from decimal import Decimal

from app import get_db, assess_risk


def analyze_existing_transactions():

    db = None
    cursor = None

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # Get all transactions in chronological order
        cursor.execute("""
            SELECT
                transaction_id,
                account_id,
                transaction_datetime,
                amount,
                region
            FROM transactions
            ORDER BY transaction_datetime ASC,
                     transaction_id ASC
        """)

        transactions = cursor.fetchall()

        alerts_created = 0

        print("\nFINANCIAL FRAUD DETECTION REPORT")
        print("-" * 55)

        for transaction in transactions:

            transaction_id = transaction["transaction_id"]

            # Calculate risk using existing rules
            score, reasons = assess_risk(
                Decimal(str(transaction["amount"])),
                transaction["account_id"],
                transaction["transaction_datetime"],
                transaction["region"],
                cursor
            )

            # Create an alert only when score is 50 or above
            if score >= 50:

                # Prevent duplicate alerts
                cursor.execute("""
                    SELECT alert_id
                    FROM alerts
                    WHERE transaction_id = %s
                """, (transaction_id,))

                existing_alert = cursor.fetchone()

                if existing_alert is None:

                    cursor.execute("""
                        INSERT INTO alerts
                        (
                            transaction_id,
                            rule_name,
                            risk_score,
                            review_status
                        )
                        VALUES (%s, %s, %s, 'Pending')
                    """, (
                        transaction_id,
                        "; ".join(reasons),
                        score
                    ))

                    alerts_created += 1

                    status = "NEW ALERT"

                else:
                    status = "ALERT ALREADY EXISTS"

            else:
                status = "NO ALERT"

            print(
                f"Transaction ID: {transaction_id} | "
                f"Risk Score: {score} | {status}"
            )

            if reasons:
                print("Reasons:", ", ".join(reasons))

        db.commit()

        print("-" * 55)
        print("Total transactions analysed:", len(transactions))
        print("New alerts generated:", alerts_created)
        print("Analysis completed successfully!")

    except Exception as error:

        if db and db.is_connected():
            db.rollback()

        print("Error:", error)

    finally:

        if cursor:
            cursor.close()

        if db and db.is_connected():
            db.close()


if __name__ == "__main__":
    analyze_existing_transactions()