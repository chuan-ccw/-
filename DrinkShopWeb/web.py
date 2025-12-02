from flask import Flask, render_template, request, redirect, url_for
import pyodbc
from datetime import date   # 為了顯示今天日期

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)

# ------------------ 資料庫連線 ------------------
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=(localdb)\MSSQLLocalDB;"
    "DATABASE=DrinkShopDB;"
    "Trusted_Connection=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# ================== 路由設定 ==================

# 首頁：index.html  （我是店家 / 我是客人）
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


# ✅ 顧客按「開始點餐」送出表單（檢查 phone）
@app.route("/customer", methods=["POST"])
def login_customer():
    phone = request.form.get("phone", "").strip()

    # -------- 1. 基本檢查：不得為空 --------
    if not phone:
        error_msg = "電話不得為空，請重新輸入。"
        return render_template(
            "customer_login.html",
            error_msg=error_msg,
            old_phone=phone
        )

    # -------- 2. 檢查是否 10 位數字 --------
    if not (phone.isdigit() and len(phone) == 10):
        error_msg = "電話需為 10 位數字（例如：0912345678），請重新輸入。"
        return render_template(
            "customer_login.html",
            error_msg=error_msg,
            old_phone=phone
        )

    # -------- 3. 通過檢查才碰資料庫 --------
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

    # 不管新舊客人，都導到點餐頁，把電話帶過去
    return redirect(url_for("order_drink", phone=phone))


# ✅ 顧客點飲料頁：order_drink.html
@app.route("/order_drink")
def order_drink():
    # 從網址上拿電話，例如 /order_drink?phone=0912...
    phone = request.args.get("phone", "")
    today = date.today().strftime("%Y-%m-%d")

    # 從資料庫抓所有飲料
    cursor.execute(
        "SELECT product_id, name, photo_url, price FROM product ORDER BY product_id"
    )
    rows = cursor.fetchall()

    products = []
    for row in rows:
        # row[2] = photo_url，目前資料表裡長這樣：static/product_images/xxx.jpg
        photo = row[2]
        if photo.startswith("static/"):
            # 換成相對於 static/ 的路徑，方便 url_for 使用
            photo = photo[len("static/"):]   # 變成 "product_images/xxx.jpg"

        products.append({
            "id": row[0],        # product_id
            "name": row[1],      # name
            "photo_url": photo,  # 例如 "product_images/8冰烏_40.jpg"
            "price": row[3],     # price
        })

    # 丟到模板
    return render_template(
        "order_drink.html",
        customer_phone=phone,
        today=today,
        products=products
    )


# 店家登入頁：admin_login.html
@app.route("/store", methods=["GET", "POST"])           # 舊的路徑（相容用）
@app.route("/admin_login", methods=["GET", "POST"])     # 新的路徑
@app.route("/admin_login.html", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        # 只顯示畫面
        return render_template("admin_login.html")

    # POST：表單送出時檢查店家 ID（簡單版，先不管密碼）
    store_id = request.form.get("shopId", "").strip()   # 對應 input name="shopId"

    cursor.execute("SELECT store_id FROM store WHERE store_id = ?", (store_id,))
    row = cursor.fetchone()

    if row:
        # TODO: 之後改成 admin_orders.html（老闆看訂單列表）
        return "店家登入成功（之後導到 admin_orders.html）"

    return "店家編號錯誤，請重新輸入。"


if __name__ == "__main__":
    app.run(debug=True)
