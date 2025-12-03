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

ADMIN_ID = "shop01"   # 這個字串就是老闆登入要輸入的 ID

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


# ✅ 顧客點飲料頁：order_drink.html
@app.route("/order_drink")
def order_drink():
    # 從網址上拿電話 & 訂單編號
    phone = request.args.get("phone", "")
    order_id = request.args.get("order_id", "")
    today = date.today().strftime("%Y-%m-%d")

    # 從資料庫抓所有飲料
    cursor.execute(
        "SELECT product_id, name, photo_url, price FROM product ORDER BY product_id"
    )
    rows = cursor.fetchall()

    products = []
    for row in rows:
        photo = row[2]
        if photo.startswith("static/"):
            photo = photo[len("static/"):]   # 變成 "product_images/xxx.jpg"

        products.append({
            "id": row[0],
            "name": row[1],
            "photo_url": photo,
            "price": row[3],
        })

    # 丟到模板
    return render_template(
        "order_drink.html",
        customer_phone=phone,
        order_id=order_id,
        today=today,
        products=products
    )


# ✅ 客人按「加入訂單」：新增一筆 item，然後跳到訂單總覽
@app.route("/add_order", methods=["POST"])
def add_order():
    phone = request.form.get("phone", "").strip()
    order_id = request.form.get("order_id", "").strip()

    if not order_id:
        # 理論上不會發生，保險用
        return redirect(url_for("customer_login"))

    # ----- 讀取表單 -----
    product_id = request.form.get("drink", "").strip()
    size = request.form.get("size", "").strip()
    ice = request.form.get("ice", "").strip()
    sweet = request.form.get("sweet", "").strip()
    topping = request.form.get("topping", "").strip()
    qty = request.form.get("qty", "").strip() or "1"
    note = request.form.get("note", "").strip()

    # 👉 1) 沒選飲品：留在同一頁，顯示「請選擇飲品」
    if not product_id:
        # 重新把商品撈出來
        cursor.execute(
            "SELECT product_id, name, photo_url, price FROM product ORDER BY product_id"
        )
        rows = cursor.fetchall()
        products = []
        for row in rows:
            photo = row[2]
            if photo.startswith("static/"):
                photo = photo[len("static/"):]
            products.append({
                "id": row[0],
                "name": row[1],
                "photo_url": photo,
                "price": row[3],
            })

        today = date.today().strftime("%Y-%m-%d")
        return render_template(
            "order_drink.html",
            customer_phone=phone,
            order_id=order_id,
            today=today,
            products=products,
            error_msg="請選擇飲品"
        )

    # 👉 2) 轉型成整數
    try:
        product_id_int = int(product_id)
        order_id_int = int(order_id)
        qty_int = int(qty)
    except ValueError:
        # 有資料轉型失敗，就回到點餐頁
        return redirect(url_for("order_drink", phone=phone, order_id=order_id))

    # 👉 3) 產生新的 item_id
    cursor.execute("SELECT ISNULL(MAX(item_id), 0) + 1 FROM item")
    new_item_id = cursor.fetchone()[0]

    # 👉 4) 寫入 item 資料表
    # 這裡假設 item 欄位：
    # item_id, order_id, product_id, size, ice, sweet, topping, qty, note
    cursor.execute(
        """
        INSERT INTO item (
            item_id, order_id, product_id,
            size, ice, sweet, topping,
            qty, note
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_item_id,
            order_id_int,
            product_id_int,
            size,
            ice,
            sweet,
            topping,
            qty_int,
            note,
        )
    )
    conn.commit()

    # 👉 5) 新增完明細，導到訂單總覽頁
    return redirect(url_for("order_summary", phone=phone, order_id=order_id_int))


# ✅ 訂單總覽頁：order_summary.html
@app.route("/order_summary")
def order_summary():
    phone = request.args.get("phone", "").strip()
    order_id = request.args.get("order_id", "").strip()

    if not order_id:
        return redirect(url_for("customer_login"))

    try:
        order_id_int = int(order_id)
    except ValueError:
        return redirect(url_for("customer_login"))

    # 撈出這張訂單的所有明細 + 商品名稱與單價
    cursor.execute(
        """
        SELECT
            i.item_id,
            p.name,
            i.size,
            i.ice,
            i.sweet,
            i.topping,
            i.qty,
            p.price
        FROM item AS i
        JOIN product AS p ON i.product_id = p.product_id
        WHERE i.order_id = ?
        ORDER BY i.item_id
        """,
        (order_id_int,)
    )
    rows = cursor.fetchall()

    items = []
    total_amount = 0

    for row in rows:
        item_id = row[0]
        product_name = row[1]
        size = row[2]
        ice = row[3]
        sweet = row[4]
        topping = row[5]
        qty = row[6]
        price = row[7]
        line_total = price * qty
        total_amount += line_total

        items.append({
            "item_id": item_id,
            "product_name": product_name,
            "size": size,
            "ice": ice,
            "sweet": sweet,
            "topping": topping,
            "qty": qty,
            "price": price,
            "line_total": line_total,
        })

    # （可選）如果 order 有 total_amount 欄位就更新
    try:
        cursor.execute(
            "UPDATE [order] SET total_amount = ? WHERE order_id = ?",
            (total_amount, order_id_int)
        )
        conn.commit()
    except Exception:
        conn.rollback()

    return render_template(
        "order_summary.html",
        customer_phone=phone,
        order_id=order_id_int,
        items=items,
        total_amount=total_amount
    )


# ✅ 更新某一筆 item 的數量
@app.route("/update_item", methods=["POST"])
def update_item():
    phone = request.form.get("phone", "").strip()
    order_id = request.form.get("order_id", "").strip()
    item_id = request.form.get("item_id", "").strip()
    qty = request.form.get("qty", "").strip()

    # 基本檢查
    if not order_id or not item_id:
        return redirect(url_for("customer_login"))

    try:
        order_id_int = int(order_id)
        item_id_int = int(item_id)
        qty_int = int(qty)
    except ValueError:
        # 如果轉型失敗，就回訂單總覽
        return redirect(url_for("order_summary", phone=phone, order_id=order_id))

    # 如果數量 <= 0 就當作刪除這筆
    if qty_int <= 0:
        cursor.execute("DELETE FROM item WHERE item_id = ?", (item_id_int,))
    else:
        cursor.execute(
            "UPDATE item SET qty = ? WHERE item_id = ?",
            (qty_int, item_id_int)
        )
    conn.commit()

    # 重新回到訂單總覽頁，讓 order_summary() 幫你重算總金額
    return redirect(url_for("order_summary", phone=phone, order_id=order_id_int))


# ✅ 刪除某一筆 item
@app.route("/delete_item", methods=["POST"])
def delete_item():
    phone = request.form.get("phone", "").strip()
    order_id = request.form.get("order_id", "").strip()
    item_id = request.form.get("item_id", "").strip()

    if not order_id or not item_id:
        return redirect(url_for("customer_login"))

    try:
        order_id_int = int(order_id)
        item_id_int = int(item_id)
    except ValueError:
        return redirect(url_for("order_summary", phone=phone, order_id=order_id))

    cursor.execute("DELETE FROM item WHERE item_id = ?", (item_id_int,))
    conn.commit()

    return redirect(url_for("order_summary", phone=phone, order_id=order_id_int))


# ✅ 結帳：算總金額、更新訂單狀態，跳到下單成功頁
@app.route("/checkout", methods=["POST"])
def checkout():
    phone = request.form.get("phone", "").strip()
    order_id = request.form.get("order_id", "").strip()

    if not order_id:
        return redirect(url_for("customer_login"))

    try:
        order_id_int = int(order_id)
    except ValueError:
        return redirect(url_for("customer_login"))

    # 1) 重新計算這張訂單的總金額
    cursor.execute(
        """
        SELECT SUM(i.qty * p.price)
        FROM item AS i
        JOIN product AS p ON i.product_id = p.product_id
        WHERE i.order_id = ?
        """,
        (order_id_int,)
    )
    row = cursor.fetchone()
    total_amount = row[0] if row and row[0] is not None else 0

    # 2) 嘗試從 [order] 撈店家編號（如果你的資料表沒這欄，會走 except）
    store_id = "未設定"
    try:
        cursor.execute("SELECT store_id FROM [order] WHERE order_id = ?", (order_id_int,))
        row2 = cursor.fetchone()
        if row2 and row2[0] is not None:
            store_id = row2[0]
    except Exception:
        store_id = "未設定"

    # 3) （可選）更新 order 的總金額 / 狀態，有這些欄位才會成功
    try:
        cursor.execute(
            "UPDATE [order] SET total_amount = ?, status = ? WHERE order_id = ?",
            (total_amount, "已下單", order_id_int)
        )
        conn.commit()
    except Exception:
        conn.rollback()

    # 4) 導到下單成功畫面
    return render_template(
        "order_success.html",
        order_id=order_id_int,
        customer_phone=phone,
        store_id=store_id,
        total_amount=total_amount
    )




# 店家登入頁：admin_login.html
@app.route("/store", methods=["GET", "POST"])           # 舊的路徑（相容用）
@app.route("/admin_login", methods=["GET", "POST"])     # 新的路徑
@app.route("/admin_login.html", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        # 只顯示畫面（預設沒有錯誤訊息）
        return render_template("admin_login.html")

    # POST：表單送出時，只檢查「固定」的店家 ID
    store_id = request.form.get("shopId", "").strip()   # 對應 input name="shopId"

    # ✅ 只要 ID 跟我們設定的一樣就給過
    if store_id == ADMIN_ID:
        # 登入成功：導到店家訂單列表頁
        return redirect(url_for("admin_orders"))
    else:
        # 登入失敗：回登入畫面並顯示錯誤訊息
        error_msg = "店家編號錯誤"
        return render_template(
            "admin_login.html",
            error_msg=error_msg,
            old_shopId=store_id,   # 把剛輸入過的 ID 填回去
        )


# 店家訂單列表頁：admin_orders.html
# 店家訂單列表頁：admin_orders.html
@app.route("/admin_order")
def admin_orders():
    orders = []

    try:
        cursor.execute(
            """
            SELECT 
                o.order_id,
                c.phone,
                ISNULL(o.total_amount, 0) AS total_amount,
                ISNULL(o.status, '未完成') AS status
            FROM [order] AS o
            LEFT JOIN customer AS c
                ON o.customer_id = c.customer_id
            ORDER BY o.order_id DESC
            """
        )
        rows = cursor.fetchall()

        for row in rows:
            orders.append({
                "order_id": row[0],
                "phone": row[1],
                "total_amount": row[2],
                "status": row[3],
            })
    except Exception:
        # 如果沒 total_amount / status 這些欄位，就先給空表
        orders = []

    # 把固定的店家 ID 一起丟進模板（之前在檔案上面有宣告 ADMIN_ID）
    return render_template("admin_order.html", orders=orders, admin_id=ADMIN_ID)





if __name__ == "__main__":
    app.run(debug=True)
