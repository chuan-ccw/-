from flask import Flask, render_template, request, redirect, url_for
import pyodbc

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)

# ---------- Azure SQL Connection Config ----------
server = 'drinkshop-sqlserver.database.windows.net,1433'
database = 'DrinkShopDB'
username = 'drinkshopadmin'
password = 'DrinkShop2025'

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# ---------- Flask Routes ----------
@app.route("/")
@app.route("/index")
@app.route("/index.html")
def index():
    return render_template("index.html")

# 顧客登入頁：customer_login.html  （輸入電話）
@app.route("/customer_login")
@app.route("/customer_login.html")
def customer_login():
    # 預設沒有錯誤訊息
    return render_template("customer_login.html")

@app.route("/store", methods=["GET", "POST"])           # 舊的路徑（相容用）
@app.route("/admin_login", methods=["GET", "POST"])     # 新的路徑
@app.route("/admin_login.html", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        # 只顯示畫面（預設沒有錯誤訊息）
        return render_template("admin_login.html")


# ✅ 顧客按「開始點餐」送出表單（檢查 phone，建立 customer + order）
@app.route("/customer", methods=["POST"])
def login_customer():
    phone = request.form.get("phone", "").strip()

    # 1. 不得為空
    if not phone:
        error_msg = "電話不得為空，請重新輸入。"
        return render_template(
            "customer_login.html",
            error_msg=error_msg,
            old_phone=phone
        )

    # 2. 檢查是否 10 位數字
    if not (phone.isdigit() and len(phone) == 10):
        error_msg = "電話需為 10 位數字（例如：0912345678），請重新輸入。"
        return render_template(
            "customer_login.html",
            error_msg=error_msg,
            old_phone=phone
        )

    # 3. 通過檢查才碰資料庫
    # 先看這個電話在不在 customer 裡
    cursor.execute(
        "SELECT customer_id FROM customer WHERE phone = ?",
        (phone,)
    )
    row = cursor.fetchone()

    if row:
        # 已經是舊客人
        customer_id = row[0]
    else:
        # 新客人：幫他創一筆資料
        cursor.execute("SELECT ISNULL(MAX(customer_id), 0) + 1 FROM customer")
        new_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO customer (customer_id, phone) VALUES (?, ?)",
            (new_id, phone)
        )
        conn.commit()
        customer_id = new_id

    # 4. 幫這次點餐建立一筆新的訂單（order）
    cursor.execute("SELECT ISNULL(MAX(order_id), 0) + 1 FROM [order]")
    new_order_id = cursor.fetchone()[0]

    # 這裡假設 [order] 至少有 (order_id, customer_id) 兩個欄位
    cursor.execute(
        "INSERT INTO [order] (order_id, customer_id) VALUES (?, ?)",
        (new_order_id, customer_id)
    )
    conn.commit()

    # 5. 導到點餐頁，把電話 & order_id 帶過去
    return redirect(url_for("order_drink", phone=phone, order_id=new_order_id))

# ---------- Main ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
