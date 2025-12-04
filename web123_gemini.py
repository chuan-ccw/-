from flask import Flask, render_template, request, redirect, url_for, session
import pyodbc
from datetime import date
import re

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)

app.secret_key = 'drinkshop_secret_key'

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

def get_db_connection():
    return pyodbc.connect(conn_str)

# ================== 路由設定 ==================

@app.route("/")
@app.route("/index")
@app.route("/index.html")
def index():
    return render_template("index.html")

# ================== 店家端 (Admin) ==================

@app.route("/admin_login", methods=["GET", "POST"])
@app.route("/admin_login.html", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        store_id = request.form.get("shopId", "").strip()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT store_id, name FROM store WHERE store_id = ?", (store_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            session['admin_store_id'] = row[0]
            session['admin_store_name'] = row[1]
            return redirect(url_for("admin_orders"))
        else:
            return render_template("admin_login.html", error_msg="店家 ID 不存在", old_shopId=store_id)
    return render_template("admin_login.html")

@app.route("/admin_orders")
def admin_orders():
    store_id = session.get('admin_store_id')
    store_name = session.get('admin_store_name')
    selected_id = request.args.get('selected_id') 

    if not store_id: return redirect(url_for("admin_login"))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 修改 SQL：加入 AND o.status = N'未完成'
    cursor.execute("""
        SELECT o.order_id, c.phone, o.status, o.tot_price
        FROM [order] o 
        LEFT JOIN customer c ON o.customer_id = c.customer_id
        WHERE o.store_id = ? 
          AND ISNULL(o.tot_price, 0) > 0 
          AND o.status = N'未完成'  -- ✅ 只撈未完成
        ORDER BY o.order_id ASC    -- 未完成的訂單通常按時間順序處理 (舊的在前)
    """, (store_id,))
    
    orders = [
        { "order_id": r[0], "phone": r[1] or "未知", "status": r[2] or "未完成", "tot_price": r[3] or 0 } 
        for r in cursor.fetchall()
    ]

    # 2. 查詢右側詳細資訊 (共用邏輯)
    selected_info, selected_items = get_order_details(conn, selected_id, store_id)

    conn.close()
    
    return render_template(
        "admin_order.html", 
        orders=orders, 
        store_id=store_id, 
        store_name=store_name,
        selected_info=selected_info,
        selected_items=selected_items
    )

# 更新狀態
@app.route("/admin_update_status", methods=["POST"])
def admin_update_status():
    store_id = session.get('admin_store_id')
    order_id = request.form.get("order_id")
    
    if store_id and order_id:
        conn = get_db_connection()
        conn.execute("UPDATE [order] SET status = N'已完成' WHERE order_id = ? AND store_id = ?", (order_id, store_id))
        conn.commit()
        conn.close()
        
    # 因為變成「已完成」了，所以在「admin_orders」頁面中它會消失
    # 我們重導回 admin_orders，不帶 selected_id，因為該筆訂單已經不在列表中了
    return redirect(url_for("admin_orders"))

# 輔助函式：避免重複寫查詢明細的程式碼
def get_order_details(conn, selected_id, store_id):
    selected_info = None
    selected_items = []
    
    if selected_id:
        cursor = conn.cursor()
        # 查 Header
        cursor.execute("""
            SELECT o.order_id, o.status, c.phone, o.tot_price
            FROM [order] o
            LEFT JOIN customer c ON o.customer_id = c.customer_id
            WHERE o.order_id = ? AND o.store_id = ?
        """, (selected_id, store_id))
        row = cursor.fetchone()
        
        if row:
            selected_info = {
                "order_id": row[0],
                "status": row[1],
                "phone": row[2] if row[2] else "未知",
                "tot_price": row[3]
            }

            # 查 Items
            cursor.execute("""
                SELECT i.item_id, p.name, i.size, i.ice, i.sugar, i.topping, i.quantity, p.price
                FROM item i 
                JOIN product p ON i.product_id = p.product_id 
                WHERE i.order_id = ?
            """, (selected_id,))
            
            tot_q = 0
            for r in cursor.fetchall():
                sub = r[7] * r[6]
                tot_q += r[6]
                selected_items.append({
                    "product_name": r[1], "size": r[2], "ice": r[3], "sugar": r[4], 
                    "topping": r[5], "quantity": r[6], "price": r[7], "subtotal": sub
                })
            selected_info['total_qty'] = tot_q
            
    return selected_info, selected_items

@app.route("/admin_history_orders")
def admin_history_orders():
    store_id = session.get('admin_store_id')
    store_name = session.get('admin_store_name')
    selected_id = request.args.get('selected_id') 

    if not store_id: return redirect(url_for("admin_login"))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. SQL：加入 AND o.status = N'已完成'
    cursor.execute("""
        SELECT o.order_id, c.phone, o.status, o.tot_price
        FROM [order] o 
        LEFT JOIN customer c ON o.customer_id = c.customer_id
        WHERE o.store_id = ? 
          AND ISNULL(o.tot_price, 0) > 0 
          AND o.status = N'已完成'  -- ✅ 只撈已完成
        ORDER BY o.order_id DESC   -- 歷史訂單通常看最新的 (新的在前)
    """, (store_id,))
    
    orders = [
        { "order_id": r[0], "phone": r[1] or "未知", "status": r[2] or "已完成", "tot_price": r[3] or 0 } 
        for r in cursor.fetchall()
    ]

    # 2. 查詢右側詳細資訊 (共用邏輯)
    selected_info, selected_items = get_order_details(conn, selected_id, store_id)

    conn.close()
    
    return render_template(
        "admin_history_orders.html",  # ✅ 導向新的歷史訂單頁面
        orders=orders, 
        store_id=store_id, 
        store_name=store_name,
        selected_info=selected_info,
        selected_items=selected_items
    )

@app.route("/admin_order_detail/<int:order_id>")
def admin_order_detail(order_id):
    if not session.get('admin_store_id'): return redirect(url_for("admin_login"))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 查詢 Item 明細
    cursor.execute("""
        SELECT i.item_id, p.name, i.size, i.ice, i.sugar, i.topping, i.quantity, p.price
        FROM item i 
        JOIN product p ON i.product_id = p.product_id 
        WHERE i.order_id = ?
    """, (order_id,))
    
    items = []
    tot_p, tot_q = 0, 0
    for r in cursor.fetchall():
        sub = r[7] * r[6]
        tot_p += sub
        tot_q += r[6]
        items.append({
            "product_name": r[1], 
            "size": r[2], 
            "ice": r[3], 
            "sugar": r[4], 
            "topping": r[5], 
            "quantity": r[6], 
            "price": r[7], 
            "subtotal": sub
        })
        
    # 2. ✅ 修正：查詢訂單 Header (加入 customer join 以取得電話)
    cursor.execute("""
        SELECT o.order_id, o.status, c.phone, o.tot_price
        FROM [order] o
        LEFT JOIN customer c ON o.customer_id = c.customer_id
        WHERE o.order_id = ?
    """, (order_id,))
    
    row = cursor.fetchone()
    if row:
        order_info = {
            "order_id": row[0],
            "status": row[1],
            "phone": row[2] if row[2] else "未知",
            "tot_price": row[3]
        }
    else:
        order_info = None

    conn.close()
    
    return render_template(
        "admin_order_detail.html", 
        items=items, 
        total_price=tot_p, 
        total_qty=tot_q, 
        order_info=order_info
    )

# ================== 客人端 (Customer) - 修改重點 ==================

# 顧客登入：customer_login.html (選店家)
@app.route("/customer_login", methods=["GET", "POST"])
@app.route("/customer_login.html", methods=["GET", "POST"])
def customer_login():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        store_id = request.form.get("store_id") # 取得使用者選擇的店家

        # Regex 檢查
        if not re.match(r"^09\d{8}$", phone):
            # 發生錯誤時，也要重新抓取店家列表回傳，不然下拉選單會空掉
            cursor.execute("SELECT store_id, name FROM store")
            stores = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]
            conn.close()
            return render_template("customer_login.html", error_msg="格式錯誤，請輸入 09 開頭的 10 位數字號碼", old_phone=phone, stores=stores)

        # 1. 檢查顧客是否存在
        cursor.execute("SELECT customer_id FROM customer WHERE phone = ?", (phone,))
        row = cursor.fetchone()
        if row:
            customer_id = row[0]
        else:
            cursor.execute("SELECT ISNULL(MAX(customer_id), 0) + 1 FROM customer")
            customer_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO customer (customer_id, phone) VALUES (?, ?)", (customer_id, phone))
            conn.commit()
        
        # 2. 在登入時直接建立訂單，並寫入 store_id
        cursor.execute("SELECT ISNULL(MAX(order_id), 0) + 1 FROM [order]")
        new_order_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO [order] (order_id, customer_id, store_id, status) VALUES (?, ?, ?, ?)",
            (new_order_id, customer_id, store_id, "未完成")
        )
        conn.commit()
        conn.close()
        
        # 3. 轉跳點餐畫面，帶入 store_id
        return redirect(url_for("order_drink", phone=phone, customer_id=customer_id, order_id=new_order_id, store_id=store_id))

    # GET 請求：撈取店家列表供選單使用
    cursor.execute("SELECT store_id, name FROM store")
    stores = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]
    conn.close()

    return render_template("customer_login.html", stores=stores)


# 點餐畫面：order_drink.html
@app.route("/order_drink")
@app.route("/order_drink.html")
def order_drink():
    phone = request.args.get("phone")
    customer_id = request.args.get("customer_id")
    order_id = request.args.get("order_id")
    store_id = request.args.get("store_id") # 接收 store_id
    
    if not phone or not customer_id or not order_id:
        return redirect(url_for("customer_login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # 查詢目前店家的名稱 (為了顯示在畫面上)
    store_name = "未知店家"
    if store_id:
        cursor.execute("SELECT name FROM store WHERE store_id = ?", (store_id,))
        row = cursor.fetchone()
        if row:
            store_name = row[0]

    # 取得所有飲品
    cursor.execute("SELECT product_id, name, photo_url, price FROM product")
    rows = cursor.fetchall()
    products = []
    for row in rows:
        raw_url = row[2] if row[2] else ""
        clean_path = raw_url[len("static/"):] if raw_url.startswith("static/") else raw_url
        final_url = url_for('static', filename=clean_path) if clean_path else ""
        products.append({"id": row[0], "name": row[1], "photo_url": final_url, "price": row[3] or 0})

    conn.close()

    return render_template(
        "order_drink.html",
        customer_phone=phone,
        customer_id=customer_id,
        order_id=order_id,
        store_id=store_id,      # 傳給前端 (hidden input)
        store_name=store_name,  # 傳給前端 (顯示用)
        products=products,
        today=date.today().strftime("%Y-%m-%d")
    )


# 加入訂單 (邏輯微調)
@app.route("/add_item", methods=["POST"])
def add_item():
    phone = request.form.get("phone")
    customer_id = request.form.get("customer_id")
    order_id = request.form.get("order_id")
    store_id = request.form.get("store_id")
    
    product_id = request.form.get("product_id")
    size = request.form.get("size")
    ice = request.form.get("ice")
    sugar = request.form.get("sugar")
    # 注意：這裡假設冷/熱的資訊，將會在前端被傳遞到 topping 這個 form 欄位中，然後一同寫入 topping 資料庫欄位。
    topping = request.form.get("topping", "無")
    quantity = request.form.get("quantity")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 寫入 item table
    cursor.execute("SELECT ISNULL(MAX(item_id), 0) + 1 FROM item")
    new_item_id = cursor.fetchone()[0]

    # 修正 SQL 語句：只包含現有的欄位
    cursor.execute("""
        INSERT INTO item (item_id, order_id, product_id, size, ice, sugar, topping, quantity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (new_item_id, order_id, product_id, size, ice, sugar, topping, quantity)) 
    
    conn.commit()
    conn.close()

    return redirect(url_for("order_drink", phone=phone, customer_id=customer_id, order_id=order_id, store_id=store_id))

# 訂單總覽 (order_summary)
@app.route("/order_summary")
def order_summary():
    phone = request.args.get("phone")
    order_id = request.args.get("order_id")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 查詢訂單明細 (確保沒有 i.temperature)
    cursor.execute("""
        SELECT i.item_id, p.name, i.size, i.ice, i.sugar, i.topping, i.quantity, p.price
        FROM item i JOIN product p ON i.product_id = p.product_id WHERE i.order_id = ?
    """, (order_id,))
    
    items = []
    tot_p, tot_q = 0, 0
    for r in cursor.fetchall():
        sub = r[7]*r[6]
        tot_p += sub
        tot_q += r[6]
        items.append({
            "product_name": r[1], 
            "size": r[2], 
            "ice": r[3], 
            "sugar": r[4], 
            "topping": r[5], # r[5] 是 i.topping
            "quantity": r[6], 
            "price": r[7], 
            "subtotal": sub
            # 這裡也不需要 temperature
        })
    
    # 2. 查詢 customer_id (供返回使用)
    cursor.execute("SELECT customer_id FROM customer WHERE phone = ?", (phone,))
    row_c = cursor.fetchone()
    cid = row_c[0] if row_c else None
    
    # 3. 查詢 store_id 與 store_name (供顯示與返回使用)
    sid = None
    store_name = "未知店家"
    
    cursor.execute("SELECT store_id FROM [order] WHERE order_id = ?", (order_id,))
    row_s = cursor.fetchone()
    if row_s:
        sid = row_s[0]
        # 再查店名
        cursor.execute("SELECT name FROM store WHERE store_id = ?", (sid,))
        row_name = cursor.fetchone()
        if row_name:
            store_name = row_name[0]

    conn.close()
    
    return render_template(
        "order_summary.html", 
        items=items, 
        total_price=tot_p, 
        total_qty=tot_q, 
        phone=phone, 
        order_id=order_id, 
        customer_id=cid, 
        store_id=sid,           # 傳回 store_id 給前端按鈕用
        store_name=store_name   # 傳回 store_name 給前端顯示用
    )

@app.route("/checkout", methods=["POST"])
def checkout():
    order_id = request.form.get("order_id")
    tot_price = request.form.get("tot_price")
    tot_amount = request.form.get("tot_amount")
    conn = get_db_connection()
    conn.execute("UPDATE [order] SET tot_price = ?, tot_amount = ?, status = N'未完成' WHERE order_id = ?", (tot_price, tot_amount, order_id))
    conn.commit(); conn.close()
    return redirect(url_for("order_success", order_id=order_id))

@app.route("/order_success")
def order_success():
    order_id = request.args.get("order_id")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 查詢訂單基本資訊 (o.order_id, s.name, o.tot_price, c.phone, s.store_id)
    cursor.execute("""
        SELECT o.order_id, s.name, o.tot_price, c.phone, s.store_id
        FROM [order] o JOIN store s ON o.store_id = s.store_id 
        LEFT JOIN customer c ON o.customer_id = c.customer_id WHERE o.order_id = ?
    """, (order_id,))
    order_info = cursor.fetchone() 

    # 查詢訂單明細 (確保欄位正確)
    cursor.execute("""
        SELECT p.name, i.size, i.ice, i.sugar, i.topping, i.quantity, p.price
        FROM item i JOIN product p ON i.product_id = p.product_id WHERE i.order_id = ?
    """, (order_id,))
    
    items = [
        {
            "product_name": r[0], 
            "size": r[1], 
            "ice": r[2], 
            "sugar": r[3], 
            "topping": r[4], 
            "quantity": r[5], 
            "price": r[6], 
            "subtotal": r[5]*r[6]
        } 
        for r in cursor.fetchall()
    ]
    
    conn.close()
    
    if not order_info:
        return redirect(url_for("customer_login"))

    return render_template(
        "order_success.html", 
        order_id=order_info[0],       
        store_name=order_info[1],     # 這是店名 (如 "50嵐 太平店")
        total_amount=order_info[2],   
        customer_phone=order_info[3], 
        store_id=order_info[4],       
        items=items                   
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)