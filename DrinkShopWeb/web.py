from flask import Flask, render_template, request, redirect, url_for
import pyodbc
from datetime import date   # 為了顯示今天日期
import random               # 產生 3 位數亂數編號



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

ADMIN_ID = "shop01"   # 店家固定 ID


# ------------------------------------------------
# 共用：把資料庫裡的 status 統一成顯示用 / 判斷用
# ------------------------------------------------
def normalize_status(raw_status):
    """
    將資料庫裡的 status 轉成：
      - display_status: '未完成' 或 '已完成'（畫面顯示）
      - is_finished   : True / False  （程式判斷）

    規則（簡單版）：
      - 只有字串剛好等於「已完成」視為完成
      - 其他（NULL、空字串…）一律當成「未完成」
    """
    raw = (raw_status or "").strip()
    if raw == "已完成":
        return "已完成", True
    return "未完成", False


# 產生不重複的 3 位數訂單編號 (字串)，例如 '001', '564'
def generate_order_code():
    while True:
        code = f"{random.randint(1, 999):03d}"  # 1~999 轉成 3 位數

        cursor.execute(
            "SELECT COUNT(*) FROM [order] WHERE order_code = ?",
            (code,)
        )
        count = cursor.fetchone()[0]
        if count == 0:
            return code


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

    # 3. 先看這個電話在不在 customer 裡
    cursor.execute(
        "SELECT customer_id FROM customer WHERE phone = ?",
        (phone,)
    )
    row = cursor.fetchone()

    if row:
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

    # 產生 3 位數隨機編號
    order_code = generate_order_code()

    # ★ 一開始就設定成「未完成」的訂單
    cursor.execute(
        "INSERT INTO [order] (order_id, customer_id, order_code, [status]) "
        "VALUES (?, ?, ?, ?)",
        (new_order_id, customer_id, order_code, "未完成")
    )
    conn.commit()

    # 5. 導到點餐頁，把電話 & order_id 帶過去
    return redirect(url_for("order_drink", phone=phone, order_id=new_order_id))


# ✅ 顧客點飲料頁：order_drink.html
@app.route("/order_drink")
def order_drink():
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
            photo = photo[len("static/"):]
        products.append({
            "id": row[0],
            "name": row[1],
            "photo_url": photo,
            "price": row[3],
        })

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
        return redirect(url_for("customer_login"))

    product_id = request.form.get("drink", "").strip()
    size = request.form.get("size", "").strip()
    ice = request.form.get("ice", "").strip()
    sweet = request.form.get("sweet", "").strip()
    topping = request.form.get("topping", "").strip()
    qty = request.form.get("qty", "").strip() or "1"
    note = request.form.get("note", "").strip()

    # 沒選飲品：留在同一頁
    if not product_id:
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

    # 轉型
    try:
        product_id_int = int(product_id)
        order_id_int = int(order_id)
        qty_int = int(qty)
    except ValueError:
        return redirect(url_for("order_drink", phone=phone, order_id=order_id))

    # 新的 item_id
    cursor.execute("SELECT ISNULL(MAX(item_id), 0) + 1 FROM item")
    new_item_id = cursor.fetchone()[0]

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

    return redirect(url_for("order_summary", phone=phone, order_id=order_id_int))


# ✅ 顧客訂單總覽頁：order_summary.html（顧客可以改數量、刪除、結帳）
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

    # 撈出這張訂單的所有明細
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

    # 更新 order.total_amount（給之後店家看的金額）
    try:
        cursor.execute(
            "UPDATE [order] SET total_amount = ? WHERE order_id = ?",
            (total_amount, order_id_int)
        )
    except Exception:
        conn.rollback()
    else:
        conn.commit()

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

    if not order_id or not item_id:
        return redirect(url_for("customer_login"))

    try:
        order_id_int = int(order_id)
        item_id_int = int(item_id)
        qty_int = int(qty)
    except ValueError:
        return redirect(url_for("order_summary", phone=phone, order_id=order_id))

    if qty_int <= 0:
        cursor.execute("DELETE FROM item WHERE item_id = ?", (item_id_int,))
    else:
        cursor.execute(
            "UPDATE item SET qty = ? WHERE item_id = ?",
            (qty_int, item_id_int)
        )
    conn.commit()

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


# ✅ 顧客結帳：算總金額、更新訂單狀態，跳到下單成功頁
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

    # 再算一次總金額
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

    # 撈 store_id（有就顯示，沒有就顯示「未設定」）
    store_id = "未設定"
    try:
        cursor.execute("SELECT store_id FROM [order] WHERE order_id = ?", (order_id_int,))
        row2 = cursor.fetchone()
        if row2 and row2[0] is not None:
            store_id = row2[0]
    except Exception:
        store_id = "未設定"

    # ✅ 設定總金額，只有「還沒設定狀態」才寫成未完成，避免之後被覆蓋掉已完成
    try:
        cursor.execute(
            """
            UPDATE [order]
            SET total_amount = ?,
                [status] = CASE
                    WHEN [status] IS NULL OR [status] = '' THEN N'未完成'
                    ELSE [status]
                END
            WHERE order_id = ?
            """,
            (total_amount, order_id_int)
        )
        conn.commit()
    except Exception:
        conn.rollback()

    return render_template(
        "order_success.html",
        order_id=order_id_int,
        customer_phone=phone,
        store_id=store_id,
        total_amount=total_amount
    )


# ------------------ 店家相關 ------------------

# 店家登入頁：admin_login.html
@app.route("/store", methods=["GET", "POST"])
@app.route("/admin_login", methods=["GET", "POST"])
@app.route("/admin_login.html", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin_login.html")

    store_id = request.form.get("shopId", "").strip()

    if store_id == ADMIN_ID:
        return redirect(url_for("admin_orders"))
    else:
        error_msg = "店家編號錯誤"
        return render_template(
            "admin_login.html",
            error_msg=error_msg,
            old_shopId=store_id,
        )


# ✅ 店家查看所有「未完成」訂單頁：admin_order.html
# ✅ 店家查看所有「未完成」訂單頁：admin_order.html
@app.route("/admin_order")
def admin_orders():
    # 1) 先撈出「未完成」的訂單（status 不是 '已完成' 的都算未完成）
    orders = []
    cursor.execute(
        """
        SELECT 
            o.order_id,
            o.order_code,
            c.phone,
            ISNULL(o.total_amount, 0) AS total_amount,
            o.[status]
        FROM [order] AS o
        LEFT JOIN customer AS c
            ON o.customer_id = c.customer_id
        WHERE 
            o.[status] IS NULL
            OR LTRIM(RTRIM(o.[status])) = N''
            OR LTRIM(RTRIM(o.[status])) NOT LIKE N'已%'   -- 不是「已…」的都當成未完成
        ORDER BY o.order_id DESC
        """
    )
    rows = cursor.fetchall()

    for row in rows:
        order_id = row[0]
        order_code = row[1]
        phone = row[2]
        total_amount = row[3]
        raw_status = row[4]

        # 顯示用狀態（這頁一定都是未完成）
        display_status = "未完成"

        # 顯示用 3 位數編號
        code = order_code if order_code else f"{order_id:03d}"

        orders.append({
            "order_id": order_id,
            "code": code,
            "phone": phone,
            "total_amount": total_amount,
            "status": display_status,
        })

    # 2) 右側詳細：如果網址有帶 ?order_id= ，就撈出那一筆（不管完成 / 未完成）
    selected_order = None
    selected_items = []
    selected_total = 0

    selected_id_str = request.args.get("order_id", "").strip()
    if selected_id_str:
        try:
            selected_id = int(selected_id_str)
        except ValueError:
            selected_id = None

        if selected_id is not None:
            # 2-1) 撈這一筆訂單的基本資料
            cursor.execute(
                """
                SELECT 
                    o.order_id,
                    o.order_code,
                    c.phone,
                    ISNULL(o.total_amount, 0) AS total_amount,
                    o.[status]
                FROM [order] AS o
                LEFT JOIN customer AS c
                    ON o.customer_id = c.customer_id
                WHERE o.order_id = ?
                """,
                (selected_id,)
            )
            row = cursor.fetchone()
            if row:
                order_id = row[0]
                order_code = row[1]
                phone = row[2]
                total_amount_db = row[3]
                raw_status = row[4] or ""

                raw_status = raw_status.strip()
                display_status = "已完成" if raw_status == "已完成" else "未完成"

                code = order_code if order_code else f"{order_id:03d}"

                selected_order = {
                    "order_id": order_id,
                    "code": code,
                    "phone": phone,
                    "total_amount": total_amount_db,
                    "status": display_status,
                }

                # 2-2) 撈這張訂單的所有品項
                cursor.execute(
                    """
                    SELECT 
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
                    (selected_id,)
                )
                item_rows = cursor.fetchall()
                for r in item_rows:
                    name, size, ice, sweet, topping, qty, price = r
                    line_total = price * qty
                    selected_total += line_total
                    selected_items.append({
                        "product_name": name,
                        "size": size,
                        "ice": ice,
                        "sweet": sweet,
                        "topping": topping,
                        "qty": qty,
                        "price": price,
                        "line_total": line_total,
                    })

                # 2-3) 順便把總金額寫回 DB
                try:
                    cursor.execute(
                        "UPDATE [order] SET total_amount = ? WHERE order_id = ?",
                        (selected_total, selected_id)
                    )
                    conn.commit()
                    selected_order["total_amount"] = selected_total
                except Exception:
                    conn.rollback()

    return render_template(
        "admin_order.html",
        orders=orders,
        admin_id=ADMIN_ID,
        selected_order=selected_order,
        selected_items=selected_items,
        selected_total=selected_total
    )



# ✅ 店家查看「歷史訂單」頁：admin_order_history.html
@app.route("/admin_order_history")
def admin_order_history():
    history = []
    cursor.execute(
    """
    SELECT 
        o.order_id,
        o.order_code,
        c.phone,
        ISNULL(o.total_amount, 0) AS total_amount,
        o.[status]
    FROM [order] AS o
    LEFT JOIN customer AS c
        ON o.customer_id = c.customer_id
    WHERE LTRIM(RTRIM(o.[status])) LIKE N'已%'   -- 開頭是「已」的都算完成
    ORDER BY o.order_id DESC
    """
)

    rows = cursor.fetchall()

    for row in rows:
        order_id = row[0]
        order_code = row[1]
        phone = row[2]
        total_amount = row[3]

        # 這頁一定是已完成
        display_status = "已完成"

        code = order_code if order_code else f"{order_id:03d}"

        history.append({
            "order_id": order_id,
            "code": code,
            "phone": phone,
            "total_amount": total_amount,
            "status": display_status,
        })

    return render_template(
        "admin_order_history.html",
        history=history,
        admin_id=ADMIN_ID
    )




# ✅ 店家按「完成」：把訂單標記為已完成，然後跳到 admin_order_detail
# ✅ 店家按「完成」：把訂單標記為已完成，然後跳到 admin_order_detail
@app.route("/admin_finish_order", methods=["POST"])
def admin_finish_order():
    order_id_str = request.form.get("order_id", "").strip()
    if not order_id_str:
        return redirect(url_for("admin_orders"))

    try:
        order_id = int(order_id_str)
    except ValueError:
        return redirect(url_for("admin_orders"))

    try:
        # 1) 直接把狀態設成「已完成」
        cursor.execute(
            "UPDATE [order] SET [status] = N'已完成' WHERE order_id = ?",
            (order_id,)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("admin_finish_order 更新狀態失敗：", e)

    # 2) 更新完後，跳到該訂單的完成詳情頁
    return redirect(url_for("admin_order_detail", order_id=order_id))



# ✅ 店家「訂單完成」頁（單筆詳情）：admin_order_detail.html
@app.route("/admin_order_detail/<int:order_id>")
def admin_order_detail(order_id):
    # 1) 這張訂單的基本資料
    cursor.execute(
        """
        SELECT 
            o.order_id,
            o.order_code,
            c.phone,
            ISNULL(o.total_amount, 0) AS total_amount,
            o.[status]
        FROM [order] AS o
        LEFT JOIN customer AS c
            ON o.customer_id = c.customer_id
        WHERE o.order_id = ?
        """,
        (order_id,)
    )
    row = cursor.fetchone()
    order = None

    if row:
        order_id_db = row[0]
        order_code = row[1]
        phone = row[2]
        total_amount_db = row[3]
        raw_status = row[4] or ""

        status_str = raw_status.strip()

        # ★ 保險：如果還不是「已完成」，在這裡再強制設一次
        if status_str != "已完成":
            try:
                cursor.execute(
                    "UPDATE [order] SET [status] = N'已完成' WHERE order_id = ?",
                    (order_id_db,)
                )
                conn.commit()
                status_str = "已完成"
            except Exception as e:
                conn.rollback()
                print("admin_order_detail 更新狀態失敗：", e)

        code = order_code if order_code else f"{order_id_db:03d}"

        order = {
            "order_id": order_id_db,
            "code": code,
            "phone": phone,
            "total_amount": total_amount_db,
            "status": status_str or "未完成",
        }

    # 2) 這張訂單的明細
    items = []
    total_amount = 0
    if order:
        cursor.execute(
            """
            SELECT 
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
            (order_id,)
        )
        rows = cursor.fetchall()
        for r in rows:
            name, size, ice, sweet, topping, qty, price = r
            line_total = price * qty
            total_amount += line_total
            items.append({
                "product_name": name,
                "size": size,
                "ice": ice,
                "sweet": sweet,
                "topping": topping,
                "qty": qty,
                "price": price,
                "line_total": line_total,
                "code": order["code"],
            })

        # 同步 total_amount 到 DB
        try:
            cursor.execute(
                "UPDATE [order] SET total_amount = ? WHERE order_id = ?",
                (total_amount, order_id)
            )
            conn.commit()
            order["total_amount"] = total_amount
        except Exception as e:
            conn.rollback()
            print("更新 total_amount 失敗：", e)

    return render_template(
        "admin_order_detail.html",
        order=order,
        items=items,
        total_amount=total_amount
    )



if __name__ == "__main__":
    app.run(debug=True)
