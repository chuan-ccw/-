import re
import pyodbc
from datetime import date
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)

# ---------- Flask session 設定 ----------
# 正式環境請改成隨機長字串，不能公開
app.secret_key = "replace-with-your-secret-key"

# ---------- Azure SQL Connection Config ----------
server = "drinkshop-sqlserver.database.windows.net,1433"
database = "DrinkShopDB"
username = "drinkshopadmin"
password = "DrinkShop2025"

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


# ---------- DB Helper 函式 ----------

def get_connection():
    """取得一個新的資料庫連線"""
    return pyodbc.connect(conn_str)


def fetchall_dict(sql, params=()):
    """查詢多筆資料，回傳 list[dict]，讓 Jinja 比較好用欄位名稱"""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        rows = []
        for r in cur.fetchall():
            rows.append(dict(zip(cols, r)))
        return rows


def fetchone_dict(sql, params=()):
    """查詢單筆資料，回傳 dict (找不到時回 {} )"""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        r = cur.fetchone()
        if not r:
            return {}
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, r))


def get_next_order_id():
    """取出 [order] 最大 order_id + 1，當作新訂單編號"""
    row = fetchone_dict("SELECT ISNULL(MAX(order_id), 0) + 1 AS next_id FROM [order]")
    return row.get("next_id", 1)


# ---------- 首頁 ----------

@app.route("/")
@app.route("/index")
@app.route("/index.html")
def index():
    return render_template("index.html")


# ============================================================
#                       店家端
# ============================================================

# ---------- 店家登入 ----------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        store_id_raw = request.form.get("store_id", "").strip()

        if not store_id_raw:
            flash("請輸入店家編號（store_id）")
            return render_template("admin_login.html")

        if not store_id_raw.isdigit():
            flash("店家編號必須是數字")
            return render_template("admin_login.html")

        store_id = int(store_id_raw)

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT store_id, name FROM store WHERE store_id = ?",
                (store_id,),
            )
            row = cur.fetchone()

        if not row:
            flash("查無此店家編號")
            return render_template("admin_login.html")

        # 登入成功，記在 session
        session["store_id"] = row[0]
        session["store_name"] = row[1]

        return redirect(url_for("admin_orders"))

    return render_template("admin_login.html")


# ---------- 店家查看所有訂單 ----------

@app.route("/admin/orders")
def admin_orders():
    store_id = session.get("store_id")
    if not store_id:
        return redirect(url_for("admin_login"))

    sql = """
        SELECT
            o.order_id,
            o.customer_id,
            c.phone AS customer_phone,
            o.status
        FROM [order] AS o
        JOIN customer AS c ON o.customer_id = c.customer_id
        WHERE o.store_id = ?
        ORDER BY o.order_id DESC;
    """
    orders = fetchall_dict(sql, (store_id,))

    return render_template(
        "admin_orders.html",
        store_name=session.get("store_name"),
        orders=orders,
    )


# ---------- 店家將訂單狀態改為「已完成」 ----------

@app.route("/admin/orders/<int:order_id>/complete", methods=["POST"])
def admin_complete_order(order_id):
    store_id = session.get("store_id")
    if not store_id:
        return redirect(url_for("admin_login"))

    with get_connection() as conn:
        cur = conn.cursor()
        # 這裡直接一刀切成「已完成」
        cur.execute(
            "UPDATE [order] SET status = ? WHERE order_id = ? AND store_id = ?",
            ("已完成", order_id, store_id),
        )
        conn.commit()

    return redirect(url_for("admin_orders"))


# ---------- 單筆訂單詳細資料 ----------

@app.route("/admin/orders/<int:order_id>")
def admin_order_detail(order_id):
    store_id = session.get("store_id")
    if not store_id:
        return redirect(url_for("admin_login"))

    items_sql = """
        SELECT
            i.item_id,
            i.order_id,
            i.product_id,
            p.name AS product_name,
            p.price,
            i.size,
            i.ice,
            i.sugar,
            i.topping,
            i.quantity
        FROM item AS i
        JOIN product AS p ON i.product_id = p.product_id
        WHERE i.order_id = ?
    """
    items = fetchall_dict(items_sql, (order_id,))

    totals_sql = """
        SELECT
            SUM(p.price * i.quantity) AS tot_price,
            SUM(i.quantity) AS tot_amount
        FROM item AS i
        JOIN product AS p ON i.product_id = p.product_id
        WHERE i.order_id = ?
    """
    totals = fetchone_dict(totals_sql, (order_id,))

    tot_price = totals.get("tot_price") or 0
    tot_amount = totals.get("tot_amount") or 0

    return render_template(
        "admin_order_detail.html",
        order_id=order_id,
        store_name=session.get("store_name"),
        items=items,
        tot_price=tot_price,
        tot_amount=tot_amount,
    )


# ============================================================
#                       客人端
# ============================================================

# ---------- 客人登入 ----------

@app.route("/customer/login", methods=["GET", "POST"])
def customer_login():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()

        # 手機格式：09 開頭 + 8 位數字
        if not re.fullmatch(r"09\d{8}", phone):
            flash("電話格式錯誤，需為 09 開頭共 10 位數字")
            return render_template("customer_login.html", phone=phone)

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT customer_id FROM customer WHERE phone = ?",
                (phone,),
            )
            row = cur.fetchone()

            if row:
                customer_id = row[0]
            else:
                # 不存在就新增一筆，只存 phone，其他欄位如果有 NOT NULL 要調整
                cur.execute(
                    "INSERT INTO customer (phone) OUTPUT inserted.customer_id VALUES (?)",
                    (phone,),
                )
                customer_id = cur.fetchone()[0]
                conn.commit()

        # 存在 session
        session["customer_id"] = customer_id
        session["customer_phone"] = phone

        # 登入新客人時，清掉舊的訂單資訊
        session.pop("current_order_id", None)
        session.pop("current_store_id", None)
        session.pop("last_order_id", None)

        return redirect(url_for("order_drink"))

    return render_template("customer_login.html")


# ---------- 客人點餐畫面 ----------

@app.route("/order/drink", methods=["GET", "POST"])
def order_drink():
    if "customer_id" not in session:
        return redirect(url_for("customer_login"))

    if "current_order_id" not in session:
        session["current_order_id"] = get_next_order_id()

    order_id = session["current_order_id"]

    stores = fetchall_dict("SELECT store_id, name FROM store ORDER BY store_id")
    products = fetchall_dict(
        "SELECT product_id, name, price, photo_url FROM product ORDER BY product_id"
    )

    if request.method == "POST":
        ...
        # 加入訂單的程式碼略

    return render_template(
        "order_drink.html",
        phone=session.get("customer_phone"),   # ✅ 顧客電話
        order_id=order_id,                     # ✅ 訂單編號
        today=date.today().isoformat(),        # ✅ 今日日期 (2025-01-01 這個會變成動態)
        stores=stores,
        products=products,
        current_store_id=session.get("current_store_id"),
    )

# ---------- 訂單細項（目前訂單） ----------

@app.route("/order/summary")
def order_summary():
    if "customer_id" not in session or "current_order_id" not in session:
        return redirect(url_for("customer_login"))

    order_id = session["current_order_id"]

    items_sql = """
        SELECT
            i.item_id,
            i.order_id,
            i.product_id,
            p.name AS product_name,
            p.price,
            i.size,
            i.ice,
            i.sugar,
            i.topping,
            i.quantity
        FROM item AS i
        JOIN product AS p ON i.product_id = p.product_id
        WHERE i.order_id = ?
    """
    items = fetchall_dict(items_sql, (order_id,))

    totals_sql = """
        SELECT
            SUM(p.price * i.quantity) AS tot_price,
            SUM(i.quantity) AS tot_amount
        FROM item AS i
        JOIN product AS p ON i.product_id = p.product_id
        WHERE i.order_id = ?
    """
    totals = fetchone_dict(totals_sql, (order_id,))

    tot_price = totals.get("tot_price") or 0
    tot_amount = totals.get("tot_amount") or 0

    return render_template(
        "order_summary.html",
        order_id=order_id,
        items=items,
        tot_price=tot_price,
        tot_amount=tot_amount,
    )


# ---------- 結帳：把資料寫入 order table ----------

@app.route("/order/checkout", methods=["POST"])
def order_checkout():
    if "customer_id" not in session or "current_order_id" not in session:
        return redirect(url_for("customer_login"))

    order_id = session["current_order_id"]
    customer_id = session["customer_id"]
    store_id = session.get("current_store_id")

    if store_id is None:
        flash("請先選擇店家再結帳")
        return redirect(url_for("order_summary"))

    totals_sql = """
        SELECT
            SUM(p.price * i.quantity) AS tot_price,
            SUM(i.quantity) AS tot_amount
        FROM item AS i
        JOIN product AS p ON i.product_id = p.product_id
        WHERE i.order_id = ?
    """
    totals = fetchone_dict(totals_sql, (order_id,))

    tot_price = totals.get("tot_price") or 0
    tot_amount = totals.get("tot_amount") or 0

    with get_connection() as conn:
        cur = conn.cursor()
        # status 一律先寫「未完成」
        cur.execute(
            """
            INSERT INTO [order] (order_id, store_id, customer_id, tot_price, tot_amount, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (order_id, store_id, customer_id, tot_price, tot_amount, "未完成"),
        )
        conn.commit()

    # 給下單成功頁面使用
    session["last_order_id"] = order_id

    return redirect(url_for("order_success"))


# ---------- 下單成功畫面 ----------

@app.route("/order/success")
def order_success():
    order_id = session.get("last_order_id")
    if not order_id:
        return redirect(url_for("customer_login"))

    order_sql = """
        SELECT
            o.order_id,
            o.store_id,
            s.name AS store_name,
            o.tot_price,
            o.tot_amount,
            o.status
        FROM [order] AS o
        JOIN store AS s ON o.store_id = s.store_id
        WHERE o.order_id = ?
    """
    order_row = fetchone_dict(order_sql, (order_id,))
    if not order_row:
        flash("查無此訂單")
        return redirect(url_for("customer_login"))

    items_sql = """
        SELECT
            i.item_id,
            i.order_id,
            i.product_id,
            p.name AS product_name,
            p.price,
            i.size,
            i.ice,
            i.sugar,
            i.topping,
            i.quantity
        FROM item AS i
        JOIN product AS p ON i.product_id = p.product_id
        WHERE i.order_id = ?
    """
    items = fetchall_dict(items_sql, (order_id,))

    return render_template(
        "order_success.html",
        order=order_row,
        items=items,
    )


# ---------- 再次訂購：清掉目前訂單，保留客人登入 ----------

@app.route("/order/again", methods=["POST"])
def order_again():
    # 保留 customer_id / phone，只清除訂單相關資料
    session.pop("current_order_id", None)
    session.pop("current_store_id", None)
    session.pop("last_order_id", None)

    return redirect(url_for("order_drink"))


# ---------- 主程式 ----------

if __name__ == "__main__":
    app.run(port=4000, debug=True)
