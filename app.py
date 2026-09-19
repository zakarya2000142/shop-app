from flask import Flask, render_template, request, redirect, session
from datetime import datetime, timedelta
import database

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "zakarya_secret_key_2026"
database.init_db()

def current_user():
    return session.get("user_id")

# ---------- ثبت‌نام و ورود ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        phone = request.form.get("phone", "")

        if not phone:
            return render_template("register.html", error="شماره موبایل الزامی است")

        if database.get_user_by_username(username):
            return render_template("register.html", error="این یوزرنیم قبلاً گرفته شده")

        if database.add_user(username, password, "", phone, "", ""):
            return redirect("/login")
        return render_template("register.html", error="خطا در ثبت‌نام")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = database.get_user(username, password)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/")
        return render_template("login.html", error="یوزرنیم یا پسورد اشتباهه")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------- داشبورد ----------

@app.route("/")
def index():
    if not current_user():
        return redirect("/login")
    uid = current_user()
    products = database.get_products(uid)
    customers = database.get_customers(uid)
    total, total_profit = database.get_total_report(uid)
    today = datetime.now().strftime("%Y-%m-%d")
    today_total, today_profit = database.get_report_by_date(uid, today)
    low_stock = [p for p in products if p["count"] < 2]
    cash_balance = database.get_cash_balance(uid)

    return render_template("index.html", products=products, customers=customers,
                           total=total, profit=total_profit,
                           today_total=today_total, today_profit=today_profit,
                           low_stock=low_stock, cash_balance=cash_balance)

# ---------- محصولات ----------

@app.route("/products")
def products():
    if not current_user():
        return redirect("/login")
    return render_template("products.html", products=database.get_products(current_user()))

@app.route("/add_product", methods=["POST"])
def add_product():
    if not current_user():
        return redirect("/login")
    database.add_product(current_user(), request.form["name"],
                         int(request.form["buy_price"]),
                         int(request.form["sell_price"]),
                         int(request.form["count"]))
    return redirect("/products")

@app.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if not current_user():
        return redirect("/login")
    uid = current_user()
    if request.method == "POST":
        database.update_product(uid, product_id, request.form["name"],
                                int(request.form["buy_price"]),
                                int(request.form["sell_price"]),
                                int(request.form["count"]))
        return redirect("/products")
    for p in database.get_products(uid):
        if p["id"] == product_id:
            return render_template("edit_product.html", product=p)

@app.route("/delete_product/<int:product_id>")
def delete_product(product_id):
    if not current_user():
        return redirect("/login")
    database.delete_product(current_user(), product_id)
    return redirect("/products")

# ---------- مشتری‌ها ----------

@app.route("/customers")
def customers():
    if not current_user():
        return redirect("/login")
    return render_template("customers.html", customers=database.get_customers(current_user()))

@app.route("/add_customer", methods=["POST"])
def add_customer():
    if not current_user():
        return redirect("/login")
    database.add_customer(current_user(), request.form["name"],
                          request.form["phone"], request.form["address"])
    return redirect("/customers")

@app.route("/edit_customer/<int:customer_id>", methods=["GET", "POST"])
def edit_customer(customer_id):
    if not current_user():
        return redirect("/login")
    uid = current_user()
    if request.method == "POST":
        database.update_customer(uid, customer_id, request.form["name"],
                                 request.form["phone"], request.form["address"])
        return redirect("/customers")
    for c in database.get_customers(uid):
        if c["id"] == customer_id:
            return render_template("edit_customer.html", customer=c)

@app.route("/delete_customer/<int:customer_id>")
def delete_customer(customer_id):
    if not current_user():
        return redirect("/login")
    database.delete_customer(current_user(), customer_id)
    return redirect("/customers")

@app.route("/add_debt/<int:customer_id>", methods=["POST"])
def add_debt(customer_id):
    if not current_user():
        return redirect("/login")
    amount = int(request.form["amount"])
    database.add_debt(current_user(), customer_id, amount)
    return redirect("/customers")

@app.route("/pay_debt/<int:customer_id>", methods=["POST"])
def pay_debt(customer_id):
    if not current_user():
        return redirect("/login")
    amount = int(request.form["amount"])
    database.pay_debt(current_user(), customer_id, amount)
    return redirect("/customers")

# ---------- فاکتورها ----------

@app.route("/invoices")
def invoices():
    if not current_user():
        return redirect("/login")
    return render_template("invoices.html", invoices=database.get_invoices(current_user()))

@app.route("/new_invoice")
def new_invoice():
    if not current_user():
        return redirect("/login")
    uid = current_user()
    return render_template("new_invoice.html",
                           products=database.get_products(uid),
                           customers=database.get_customers(uid))

@app.route("/create_invoice", methods=["POST"])
def create_invoice():
    if not current_user():
        return redirect("/login")
    uid = current_user()
    customer_id = int(request.form["customer_id"])
    items = []
    for key in request.form:
        if key.startswith("count_"):
            product_id = int(key.replace("count_", ""))
            count = int(request.form[key])
            if count > 0:
                for p in database.get_products(uid):
                    if p["id"] == product_id:
                        items.append({
                            "product_id": product_id,
                            "count": count,
                            "sell_price": p["sell_price"],
                            "buy_price": p["buy_price"]
                        })
    if items:
        database.add_invoice(uid, customer_id, items)
    return redirect("/invoices")

@app.route("/invoice/<int:invoice_id>")
def invoice_detail(invoice_id):
    if not current_user():
        return redirect("/login")
    uid = current_user()
    invoices = database.get_invoices(uid)
    invoice = None
    for i in invoices:
        if i["id"] == invoice_id:
            invoice = i
            break
    items = database.get_invoice_items(invoice_id)
    return render_template("invoice_detail.html", invoice=invoice, items=items)

@app.route("/delete_invoice/<int:invoice_id>")
def delete_invoice(invoice_id):
    if not current_user():
        return redirect("/login")
    database.delete_invoice(current_user(), invoice_id)
    return redirect("/invoices")

# ---------- صندوق ----------

@app.route("/cash", methods=["GET", "POST"])
def cash():
    if not current_user():
        return redirect("/login")
    uid = current_user()
    if request.method == "POST":
        type_ = request.form["type"]
        amount = int(request.form["amount"])
        description = request.form.get("description", "")
        database.add_cash(uid, type_, amount, description)
        return redirect("/cash")
    return render_template("cash.html",
                           cash_list=database.get_cash(uid),
                           balance=database.get_cash_balance(uid))

# ---------- گزارش‌ها ----------

@app.route("/reports")
def reports():
    if not current_user():
        return redirect("/login")
    uid = current_user()
    today = datetime.now().strftime("%Y-%m-%d")
    week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    year = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    total, total_profit = database.get_total_report(uid)
    t_total, t_profit = database.get_report_by_date(uid, today)
    w_total, w_profit = database.get_report_by_date(uid, week)
    m_total, m_profit = database.get_report_by_date(uid, month)
    y_total, y_profit = database.get_report_by_date(uid, year)

    return render_template("reports.html",
                           total=total, profit=total_profit,
                           t_total=t_total, t_profit=t_profit,
                           w_total=w_total, w_profit=w_profit,
                           m_total=m_total, m_profit=m_profit,
                           y_total=y_total, y_profit=y_profit)

# ---------- پشتیبانی ----------

@app.route("/support")
def support():
    if not current_user():
        return redirect("/login")
    return render_template("support.html")

if __name__ == "__main__":
    app.run()

---

### الان:

**۱. برو توی گیت‌هاب → `shop-app` → `app.py` → Edit.**

**۲. کل محتوا رو پاک کن.**

**۳. این کد رو جاش بذار.**

**۴. Commit changes.**

**۵. بزن `بعدی` تا فایل بعدی رو بفرستم.**

---

اوکی؟ 😎
