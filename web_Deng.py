from flask import Flask, render_template, request
import pyodbc

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=(localdb)\MSSQLLocalDB;"
    "DATABASE=DrinkShopDB;"
    "Trusted_Connection=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()


# ========= 路由設定 =========

# 首頁：我是店家 / 我是客人
@app.route("/")
def index():
    return render_template("first.html")


# 顧客登入頁（輸入電話）
@app.route("/customer_page")
@app.route("/customer_page.html")   # 讓 /customer_page.html 也可以用
def customer_page():
    return render_template("customer_page.html")



# 顧客按「開始點餐」送出表單
@app.route("/customer", methods=["POST"])
def login_customer():
    phone = request.form.get("phone", "").strip()

    if not phone:
        return "電話不得為空，請返回上一頁重新輸入。"

    cursor.execute("SELECT phone FROM customer")
    rows = cursor.fetchall()

    for row in rows:
        if phone == row[0]:
            # 找到這個電話，就進到點餐頁面（先用簡單的 order.html）
            return render_template("customer_order.html")

    # 沒找到
    return "找不到這個電話，請先向店家註冊或重新輸入。"


# 店家登入頁（GET 顯示畫面、POST 檢查 store_id）
@app.route("/store")
@app.route("/shop_login.html")
def login_store():
    if request.method == "GET":
        return render_template("shop_login.html")

    store_id = request.form.get("store_id", "").strip()

    cursor.execute("SELECT store_id FROM store")
    rows = cursor.fetchall()

    for row in rows:
        if store_id == str(row[0]):
            return render_template("customer_order.html")

    return "店家編號錯誤，請重新輸入。"


if __name__ == "__main__":
    app.run(debug=True)
