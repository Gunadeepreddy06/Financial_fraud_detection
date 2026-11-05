import os

from datetime import datetime
from decimal import Decimal, InvalidOperation

import mysql.connector

from flask import (
    Flask,
    jsonify,
    request,
    render_template,
    send_from_directory
)

from dotenv import load_dotenv

import analysis


load_dotenv()

app = Flask(__name__)


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db():

    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "financial_risk_db")
    )


# ==========================================
# HOME PAGE
# ==========================================

@app.get("/")
def home():

    return render_template("index.html")


# ==========================================
# DISPLAY CHARTS
# ==========================================

@app.get("/charts/<path:filename>")
def get_chart(filename):

    return send_from_directory("charts", filename)


# ==========================================
# RISK ASSESSMENT
# ==========================================

def assess_risk(amount, account_id, tx_time, region, cursor):

    score = 0
    reasons = []

    # Rule 1: High transaction amount

    if amount >= Decimal("50000"):

        score += 50

        reasons.append("High transaction amount")

    # Rule 2: High transaction frequency

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM transactions
        WHERE account_id = %s
        AND transaction_datetime >=
            DATE_SUB(%s, INTERVAL 1 HOUR)
        AND transaction_datetime < %s
        """,
        (account_id, tx_time, tx_time)
    )

    earlier_count = cursor.fetchone()["total"]

    if earlier_count >= 4:

        score += 30

        reasons.append("High transaction frequency")

    # Rule 3: Different transaction region

    cursor.execute(
        """
        SELECT region
        FROM transactions
        WHERE account_id = %s
        AND transaction_datetime < %s
        ORDER BY transaction_datetime DESC,
                 transaction_id DESC
        LIMIT 1
        """,
        (account_id, tx_time)
    )

    previous = cursor.fetchone()

    if (
        previous
        and previous["region"]
        and region
        and previous["region"].strip().casefold()
        != region.strip().casefold()
    ):

        score += 20

        reasons.append(
            "Region differs from previous transaction"
        )

    return min(score, 100), reasons


# ==========================================
# CHART REGENERATION
# ==========================================

def update_charts():

    try:

        analysis.main()

        return True

    except Exception:

        app.logger.exception(
            "Chart regeneration failed"
        )

        return False


# ==========================================
# GET ALL TRANSACTIONS
# ==========================================

@app.get("/transactions")
def get_transactions():

    db = None
    cursor = None

    try:

        db = get_db()

        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                transaction_id,
                account_id,
                transaction_datetime,
                amount,
                transaction_type,
                channel,
                region
            FROM transactions
            ORDER BY transaction_datetime DESC,
                     transaction_id DESC
            """
        )

        rows = cursor.fetchall()

        for row in rows:

            row["amount"] = float(row["amount"])

            row["transaction_datetime"] = (
                row["transaction_datetime"].isoformat(sep=" ")
            )

        return jsonify(rows)

    except mysql.connector.Error:

        app.logger.exception(
            "Unable to retrieve transactions"
        )

        return jsonify({
            "error": "Database operation failed"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if db and db.is_connected():
            db.close()


# ==========================================
# POST - ADD TRANSACTION
# ==========================================

@app.post("/transactions")
def add_transaction():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):

        return jsonify({
            "error": "Send a JSON object"
        }), 400

    required = [
        "account_id",
        "transaction_datetime",
        "amount",
        "transaction_type",
        "channel"
    ]

    if any(key not in data for key in required):

        return jsonify({
            "error": "Missing required fields",
            "required": required
        }), 400

    try:

        account_id = int(data["account_id"])

        amount = Decimal(str(data["amount"]))

        tx_time = datetime.fromisoformat(
            str(data["transaction_datetime"])
        )

        tx_type = str(
            data["transaction_type"]
        ).strip().upper()

        channel = str(data["channel"]).strip()

        region = data.get("region")

        if account_id <= 0:
            raise ValueError()

        if (
            not amount.is_finite()
            or amount <= 0
            or amount > Decimal("9999999999.99")
        ):
            raise ValueError()

        if tx_type not in {
            "DEPOSIT",
            "WITHDRAWAL",
            "TRANSFER"
        }:
            raise ValueError()

        if not channel or len(channel) > 30:
            raise ValueError()

        if region is not None:

            if not isinstance(region, str) or len(region) > 60:
                raise ValueError()

            region = region.strip() or None

    except (
        ValueError,
        TypeError,
        InvalidOperation,
        OverflowError
    ):

        return jsonify({
            "error": "Invalid transaction details"
        }), 400

    db = None
    cursor = None

    try:

        db = get_db()

        cursor = db.cursor(dictionary=True)

        # Check account

        cursor.execute(
            """
            SELECT account_id
            FROM accounts
            WHERE account_id = %s
            """,
            (account_id,)
        )

        if cursor.fetchone() is None:

            return jsonify({
                "error": "Account not found"
            }), 404

        # Calculate risk

        score, reasons = assess_risk(
            amount,
            account_id,
            tx_time,
            region,
            cursor
        )

        # Insert transaction

        cursor.execute(
            """
            INSERT INTO transactions (
                account_id,
                transaction_datetime,
                amount,
                transaction_type,
                channel,
                region
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                account_id,
                tx_time,
                amount,
                tx_type,
                channel,
                region
            )
        )

        transaction_id = cursor.lastrowid

        alert_id = None

        # Create fraud alert

        if score >= 50:

            cursor.execute(
                """
                INSERT INTO alerts (
                    transaction_id,
                    rule_name,
                    risk_score,
                    review_status
                )
                VALUES (%s, %s, %s, 'Pending')
                """,
                (
                    transaction_id,
                    "; ".join(reasons),
                    score
                )
            )

            alert_id = cursor.lastrowid

        db.commit()

        charts_updated = update_charts()

        return jsonify({

            "message": "Transaction recorded",

            "transaction_id": transaction_id,

            "risk_score": score,

            "risk_reasons": reasons,

            "alert_id": alert_id,

            "charts_updated": charts_updated

        }), 201

    except mysql.connector.Error:

        if db and db.is_connected():
            db.rollback()

        app.logger.exception(
            "Unable to add transaction"
        )

        return jsonify({
            "error": "Database operation failed"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if db and db.is_connected():
            db.close()


# ==========================================
# PUT - UPDATE TRANSACTION
# ==========================================

@app.put("/transactions/<int:transaction_id>")
def update_transaction(transaction_id):

    data = request.get_json(silent=True)

    if not isinstance(data, dict):

        return jsonify({
            "error": "Send a JSON object"
        }), 400

    required = [
        "account_id",
        "transaction_datetime",
        "amount",
        "transaction_type",
        "channel"
    ]

    if any(key not in data for key in required):

        return jsonify({
            "error": "Missing required fields",
            "required": required
        }), 400

    try:

        account_id = int(data["account_id"])

        amount = Decimal(str(data["amount"]))

        tx_time = datetime.fromisoformat(
            str(data["transaction_datetime"])
        )

        tx_type = str(
            data["transaction_type"]
        ).strip().upper()

        channel = str(data["channel"]).strip()

        region = data.get("region")

        if account_id <= 0:
            raise ValueError()

        if (
            not amount.is_finite()
            or amount <= 0
            or amount > Decimal("9999999999.99")
        ):
            raise ValueError()

        if tx_type not in {
            "DEPOSIT",
            "WITHDRAWAL",
            "TRANSFER"
        }:
            raise ValueError()

        if not channel or len(channel) > 30:
            raise ValueError()

        if region is not None:

            if not isinstance(region, str) or len(region) > 60:
                raise ValueError()

            region = region.strip() or None

    except (
        ValueError,
        TypeError,
        InvalidOperation,
        OverflowError
    ):

        return jsonify({
            "error": "Invalid transaction details"
        }), 400

    db = None
    cursor = None

    try:

        db = get_db()

        cursor = db.cursor(dictionary=True)

        # Check transaction

        cursor.execute(
            """
            SELECT transaction_id
            FROM transactions
            WHERE transaction_id = %s
            """,
            (transaction_id,)
        )

        if cursor.fetchone() is None:

            return jsonify({
                "error": "Transaction not found"
            }), 404

        # Check account

        cursor.execute(
            """
            SELECT account_id
            FROM accounts
            WHERE account_id = %s
            """,
            (account_id,)
        )

        if cursor.fetchone() is None:

            return jsonify({
                "error": "Account not found"
            }), 404

        # Calculate risk

        score, reasons = assess_risk(
            amount,
            account_id,
            tx_time,
            region,
            cursor
        )

        # Update transaction

        cursor.execute(
            """
            UPDATE transactions
            SET account_id = %s,
                transaction_datetime = %s,
                amount = %s,
                transaction_type = %s,
                channel = %s,
                region = %s
            WHERE transaction_id = %s
            """,
            (
                account_id,
                tx_time,
                amount,
                tx_type,
                channel,
                region,
                transaction_id
            )
        )

        # Check existing alert

        cursor.execute(
            """
            SELECT alert_id
            FROM alerts
            WHERE transaction_id = %s
            """,
            (transaction_id,)
        )

        existing_alert = cursor.fetchone()

        alert_id = None

        if score >= 50:

            rule_name = "; ".join(reasons)

            if existing_alert:

                alert_id = existing_alert["alert_id"]

                cursor.execute(
                    """
                    UPDATE alerts
                    SET rule_name = %s,
                        risk_score = %s,
                        review_status = 'Pending'
                    WHERE alert_id = %s
                    """,
                    (
                        rule_name,
                        score,
                        alert_id
                    )
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO alerts (
                        transaction_id,
                        rule_name,
                        risk_score,
                        review_status
                    )
                    VALUES (%s, %s, %s, 'Pending')
                    """,
                    (
                        transaction_id,
                        rule_name,
                        score
                    )
                )

                alert_id = cursor.lastrowid

        elif existing_alert:

            cursor.execute(
                """
                DELETE FROM alerts
                WHERE transaction_id = %s
                """,
                (transaction_id,)
            )

        db.commit()

        charts_updated = update_charts()

        return jsonify({

            "message": "Transaction updated successfully",

            "transaction_id": transaction_id,

            "risk_score": score,

            "risk_reasons": reasons,

            "alert_id": alert_id,

            "charts_updated": charts_updated

        }), 200

    except mysql.connector.Error:

        if db and db.is_connected():
            db.rollback()

        app.logger.exception(
            "Unable to update transaction"
        )

        return jsonify({
            "error": "Database operation failed"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if db and db.is_connected():
            db.close()


# ==========================================
# DELETE - DELETE TRANSACTION
# ==========================================

@app.delete("/transactions/<int:transaction_id>")
def delete_transaction(transaction_id):

    db = None
    cursor = None

    try:

        db = get_db()

        cursor = db.cursor()

        # Check transaction exists

        cursor.execute(
            """
            SELECT transaction_id
            FROM transactions
            WHERE transaction_id = %s
            """,
            (transaction_id,)
        )

        transaction = cursor.fetchone()

        if transaction is None:

            return jsonify({
                "error": "Transaction not found"
            }), 404

        # Delete associated alerts first

        cursor.execute(
            """
            DELETE FROM alerts
            WHERE transaction_id = %s
            """,
            (transaction_id,)
        )

        # Delete transaction

        cursor.execute(
            """
            DELETE FROM transactions
            WHERE transaction_id = %s
            """,
            (transaction_id,)
        )

        db.commit()

        charts_updated = update_charts()

        return jsonify({

            "message": "Transaction deleted successfully",

            "transaction_id": transaction_id,

            "charts_updated": charts_updated

        }), 200

    except mysql.connector.Error:

        if db and db.is_connected():
            db.rollback()

        app.logger.exception(
            "Unable to delete transaction"
        )

        return jsonify({
            "error": "Database operation failed"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if db and db.is_connected():
            db.close()


# ==========================================
# GET - ALL ALERTS
# ==========================================

@app.get("/alerts")
def get_alerts():

    db = None
    cursor = None

    try:

        db = get_db()

        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                a.alert_id,
                a.transaction_id,
                a.rule_name,
                a.risk_score,
                a.review_status,
                a.created_at,
                t.account_id,
                t.amount,
                t.transaction_datetime,
                t.region
            FROM alerts a
            JOIN transactions t
                ON a.transaction_id = t.transaction_id
            ORDER BY a.created_at DESC,
                     a.alert_id DESC
            """
        )

        rows = cursor.fetchall()

        for row in rows:

            row["amount"] = float(row["amount"])

            row["transaction_datetime"] = (
                row["transaction_datetime"].isoformat(sep=" ")
            )

            row["created_at"] = (
                row["created_at"].isoformat(sep=" ")
            )

        return jsonify(rows)

    except mysql.connector.Error:

        app.logger.exception(
            "Unable to retrieve alerts"
        )

        return jsonify({
            "error": "Database operation failed"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if db and db.is_connected():
            db.close()


# ==========================================
# PATCH - UPDATE ALERT STATUS
# ==========================================

@app.patch("/alerts/<int:alert_id>")
def update_alert(alert_id):

    data = request.get_json(silent=True)

    if not isinstance(data, dict):

        return jsonify({
            "error": "Send a JSON object"
        }), 400

    status = data.get("review_status")

    allowed_statuses = {
        "Pending",
        "Reviewed",
        "Escalated",
        "Cleared"
    }

    if status not in allowed_statuses:

        return jsonify({
            "error": "Invalid review status"
        }), 400

    db = None
    cursor = None

    try:

        db = get_db()

        cursor = db.cursor()

        cursor.execute(
            """
            UPDATE alerts
            SET review_status = %s
            WHERE alert_id = %s
            """,
            (status, alert_id)
        )

        if cursor.rowcount == 0:

            cursor.execute(
                """
                SELECT alert_id
                FROM alerts
                WHERE alert_id = %s
                """,
                (alert_id,)
            )

            if cursor.fetchone() is None:

                return jsonify({
                    "error": "Alert not found"
                }), 404

        db.commit()

        return jsonify({

            "message": "Alert updated successfully",

            "alert_id": alert_id,

            "review_status": status

        }), 200

    except mysql.connector.Error:

        if db and db.is_connected():
            db.rollback()

        app.logger.exception(
            "Unable to update alert"
        )

        return jsonify({
            "error": "Database operation failed"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if db and db.is_connected():
            db.close()


# ==========================================
# GET - FINANCIAL SUMMARY
# ==========================================

@app.get("/summary")
def summary():

    db = None
    cursor = None

    try:

        db = get_db()

        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                COUNT(*) AS transaction_count,
                COALESCE(SUM(amount), 0) AS total_amount,
                COALESCE(AVG(amount), 0) AS average_amount
            FROM transactions
            """
        )

        totals = cursor.fetchone()

        cursor.execute(
            """
            SELECT COUNT(*) AS alert_count
            FROM alerts
            WHERE review_status = 'Pending'
            """
        )

        pending = cursor.fetchone()["alert_count"]

        return jsonify({

            "transaction_count": int(
                totals["transaction_count"]
            ),

            "total_amount": float(
                totals["total_amount"]
            ),

            "average_amount": float(
                totals["average_amount"]
            ),

            "pending_alerts": int(pending)

        })

    except mysql.connector.Error:

        app.logger.exception(
            "Unable to retrieve summary"
        )

        return jsonify({
            "error": "Database operation failed"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if db and db.is_connected():
            db.close()


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )