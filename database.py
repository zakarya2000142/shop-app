import sqlite3
from datetime import datetime

DB_NAME = "shop.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        security_question TEXT,
        security_answer TEXT,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        buy_price INTEGER NOT NULL,
        sell_price INTEGER NOT NULL,
        count INTEGER NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        debt INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        customer_id INTEGER,
        date TEXT NOT NULL,
        total_amount INTEGER NOT NULL,
        total_profit INTEGER NOT NULL,
        payment_type TEXT DEFAULT 'cash'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        count INTEGER NOT NULL,
        sell_price INTEGER NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cash (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT NOT NULL,
        amount INTEGER NOT NULL,
        description TEXT,
        date TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS debt_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        customer_id INTEGER,
        amount INTEGER NOT NULL,
        date TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def add_user(username, password, email="", phone="", security_question="", security_answer=""):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password, email, phone, security_question, security_answer, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, password, email, phone, security_question, security_answer, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def get_user(username, password):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    ).fetchone()
    conn.close()
    return row

def get_user_by_username(username):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return row

def update_user_password(user_id, new_password):
    conn = get_connection()
    conn.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))
    conn.commit()
    conn.close()

def add_product(user_id, name, buy_price, sell_price, count):
    conn = get_connection()
    conn.execute(
        "INSERT INTO products (user_id, name, buy_price, sell_price, count) VALUES (?, ?, ?, ?, ?)",
        (user_id, name, buy_price, sell_price, count)
    )
    conn.commit()
    conn.close()

def get_products(user_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return rows

def update_product(user_id, product_id, name, buy_price, sell_price, count):
    conn = get_connection()
    conn.execute("""
        UPDATE products SET name = ?, buy_price = ?, sell_price = ?, count = ?
        WHERE id = ? AND user_id = ?
    """, (name, buy_price, sell_price, count, product_id, user_id))
    conn.commit()
    conn.close()

def delete_product(user_id, product_id):
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id = ? AND user_id = ?", (product_id, user_id))
    conn.commit()
    conn.close()

def add_customer(user_id, name, phone, address):
    conn = get_connection()
    conn.execute(
        "INSERT INTO customers (user_id, name, phone, address, debt) VALUES (?, ?, ?, ?, 0)",
        (user_id, name, phone, address)
    )
    conn.commit()
    conn.close()

def get_customers(user_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM customers WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return rows

def update_customer(user_id, customer_id, name, phone, address):
    conn = get_connection()
    conn.execute("""
        UPDATE customers SET name = ?, phone = ?, address = ?
        WHERE id = ? AND user_id = ?
    """, (name, phone, address, customer_id, user_id))
    conn.commit()
    conn.close()

def delete_customer(user_id, customer_id):
    conn = get_connection()
    conn.execute("DELETE FROM customers WHERE id = ? AND user_id = ?", (customer_id, user_id))
    conn.commit()
    conn.close()

def add_debt(user_id, customer_id, amount):
    conn = get_connection()
    conn.execute("UPDATE customers SET debt = debt + ? WHERE id = ? AND user_id = ?",
                 (amount, customer_id, user_id))
    conn.commit()
    conn.close()

def pay_debt(user_id, customer_id, amount):
    conn = get_connection()
    conn.execute("UPDATE customers SET debt = debt - ? WHERE id = ? AND user_id = ?",
                 (amount, customer_id, user_id))
    conn.execute(
        "INSERT INTO debt_payments (user_id, customer_id, amount, date) VALUES (?, ?, ?, ?)",
        (user_id, customer_id, amount, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()

def add_invoice(user_id, customer_id, items, payment_type="cash"):
    conn = get_connection()
    cursor = conn.cursor()

    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    total_amount = 0
    total_profit = 0

    for item in items:
        total_amount += item["sell_price"] * item["count"]
        total_profit += (item["sell_price"] - item["buy_price"]) * item["count"]

    cursor.execute("""
        INSERT INTO invoices (user_id, customer_id, date, total_amount, total_profit, payment_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, customer_id, date, total_amount, total_profit, payment_type))

    invoice_id = cursor.lastrowid

    for item in items:
        cursor.execute("""
            INSERT INTO invoice_items (invoice_id, product_id, count, sell_price)
            VALUES (?, ?, ?, ?)
        """, (invoice_id, item["product_id"], item["count"], item["sell_price"]))

        cursor.execute("UPDATE products SET count = count - ? WHERE id = ?",
                       (item["count"], item["product_id"]))

    if payment_type == "credit":
        cursor.execute("UPDATE customers SET debt = debt + ? WHERE id = ? AND user_id = ?",
                       (total_amount, customer_id, user_id))

    conn.commit()
    conn.close()
    return invoice_id

def get_invoices(user_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.*, c.name as customer_name
        FROM invoices i
        LEFT JOIN customers c ON i.customer_id = c.id
        WHERE i.user_id = ?
        ORDER BY i.id DESC
    """, (user_id,)).fetchall()
    conn.close()
    return rows

def get_invoice_items(invoice_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT ii.*, p.name as product_name
        FROM invoice_items ii
        JOIN products p ON ii.product_id = p.id
        WHERE ii.invoice_id = ?
    """, (invoice_id,)).fetchall()
    conn.close()
    return rows

def delete_invoice(user_id, invoice_id):
    conn = get_connection()
    cursor = conn.cursor()

    items = cursor.execute(
        "SELECT product_id, count FROM invoice_items WHERE invoice_id = ?",
        (invoice_id,)
    ).fetchall()

    for item in items:
        cursor.execute("UPDATE products SET count = count + ? WHERE id = ?",
                       (item["count"], item["product_id"]))

    cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
    cursor.execute("DELETE FROM invoices WHERE id = ? AND user_id = ?", (invoice_id, user_id))

    conn.commit()
    conn.close()

def add_cash(user_id, type_, amount, description=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO cash (user_id, type, amount, description, date) VALUES (?, ?, ?, ?, ?)",
        (user_id, type_, amount, description, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()

def get_cash(user_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM cash WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    conn.close()
    return rows

def get_cash_balance(user_id):
    conn = get_connection()
    income = conn.execute("SELECT SUM(amount) FROM cash WHERE user_id = ? AND type = 'in'", (user_id,)).fetchone()[0] or 0
    expense = conn.execute("SELECT SUM(amount) FROM cash WHERE user_id = ? AND type = 'out'", (user_id,)).fetchone()[0] or 0
    conn.close()
    return income - expense

def get_total_report(user_id):
    conn = get_connection()
    cash = conn.execute("""
        SELECT SUM(total_amount) as total, SUM(total_profit) as profit
        FROM invoices WHERE user_id = ? AND payment_type = 'cash'
    """, (user_id,)).fetchone()
    debt = conn.execute("""
        SELECT SUM(amount) as total FROM debt_payments WHERE user_id = ?
    """, (user_id,)).fetchone()
    conn.close()
    total = (cash["total"] or 0) + (debt["total"] or 0)
    profit = cash["profit"] or 0
    return total, profit

def get_report_by_date(user_id, start_date):
    conn = get_connection()
    cash = conn.execute("""
        SELECT SUM(total_amount) as total, SUM(total_profit) as profit
        FROM invoices WHERE user_id = ? AND date >= ? AND payment_type = 'cash'
    """, (user_id, start_date)).fetchone()
    debt = conn.execute("""
        SELECT SUM(amount) as total FROM debt_payments WHERE user_id = ? AND date >= ?
    """, (user_id, start_date)).fetchone()
    conn.close()
    total = (cash["total"] or 0) + (debt["total"] or 0)
    profit = cash["profit"] or 0
    return total, profit
