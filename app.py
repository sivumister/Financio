import sqlite3
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
DATABASE = Path(__file__).with_name("fintrack.db")


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                amount REAL NOT NULL CHECK (amount > 0),
                currency TEXT NOT NULL CHECK (currency IN ('USD', 'ZiG')),
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                transaction_date TEXT NOT NULL
            )
            """
        )


@app.route("/")
def dashboard():
    with get_connection() as connection:
        transactions = connection.execute(
            """
            SELECT type, amount, currency, category, description, transaction_date
            FROM transactions
            ORDER BY transaction_date DESC, id DESC
            """
        ).fetchall()

        balances = {"USD": 0.0, "ZiG": 0.0}
        rows = connection.execute(
            """
            SELECT currency,
                   SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END) AS balance
            FROM transactions
            GROUP BY currency
            """
        ).fetchall()

    for row in rows:
        balances[row["currency"]] = row["balance"] or 0.0

    return render_template(
        "index.html",
        transactions=transactions,
        balances=balances,
    )


@app.route("/transactions", methods=["POST"])
def add_transaction():
    transaction_type = request.form.get("type", "")
    currency = request.form.get("currency", "")
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    transaction_date = request.form.get("transaction_date", "").strip()

    try:
        amount = float(request.form.get("amount", ""))
    except ValueError:
        return "Please enter a valid amount.", 400

    if transaction_type not in {"income", "expense"}:
        return "Please choose income or expense.", 400
    if currency not in {"USD", "ZiG"}:
        return "Please choose USD or ZiG.", 400
    if amount <= 0:
        return "Amount must be greater than zero.", 400
    if not all([category, description, transaction_date]):
        return "Please complete all transaction fields.", 400

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO transactions
                (type, amount, currency, category, description, transaction_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_type,
                amount,
                currency,
                category,
                description,
                transaction_date,
            ),
        )

    return redirect(url_for("dashboard"))


initialize_database()


if __name__ == "__main__":
    app.run(debug=True)