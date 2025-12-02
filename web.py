from flask import *
import pyodbc

app = Flask(__name__)

conn = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=你的伺服器名稱;'
    'DATABASE=資料庫名稱;'
    'UID=帳號;PWD=密碼'
)

cursor = conn.cursor()
order_id = -1
customer_id = -1
store_id = -1


@app.route("/")
def first():        
    return render_template("first.html")


@app.route("/customer_login.html")
@app.route("/customer_login",methods=['POST']) #客人登入介面
def customer_login():    
    global customer_id
    global order_id
    if request.method == 'POST':
        phone = request.form.get("phone")

        cursor.execute("SELECT phone FROM customer WHERE phone=?",(phone,))
        rows = cursor.fetchall()

        if not rows :
            return "customer電話錯誤"
        else:
            cursor.execute("SELECT customer_id FROM customer WHERE phone=?",(phone,))
            rows = cursor.fetchall()
            customer_id = rows[0][0]
            cursor.execute("INSERT INTO order (customer_id) VALUES (?)",(customer_id,))
            conn.commit() 
            order_id = cursor.lastrowid
            return render_template("order_drink.html")
            
    return render_template("customer_login.html")
    

@app.route("/admin_login.html")
@app.route("/admin_login",methods=['GET','POST']) #店家登入介面
def admin_login():
    global store_id    
    if request.method == 'POST':
        store_id = request.form.get("store_id")

        cursor.execute("SELECT store_id FROM store WHERE store_id=?",(store_id,))
        rows = cursor.fetchall()

        if not rows :
            return "store id錯誤"
        else:
            return render_template("admin_order.html")
            
    return render_template("admin_login.html")
    

@app.route("/product_name",methods=['POST']) #客人選擇飲料(下拉式選單)
def product_name():    
    cursor.execute("SELECT product.name FROM product")
    rows = cursor.fetchall() 
    return render_template("customer_order.html",items=rows)

@app.route("/store_name",methods=['POST']) #客人選擇店家(下拉式選單)
def store_name():    
    cursor.execute("SELECT store.name FROM store")
    rows = cursor.fetchall() 
    return render_template("customer_order.html",items=rows)

@app.route("/order_drink.html")
@app.route("/order_drink",methods=['POST']) #客人客製化頁面
def order_drink():    
    if request.method == 'POST':
        product_name = request.form.get("product_name")
        cursor.execute("SELECT photo FROM product WHERE name=?",(product_name,))
        rows = cursor.fetchall() 
        return render_template("order_drink.html",items=rows)


    return render_template("order_drink.html")

@app.route("/add_order",methods=['GET','POST']) #客人按下加入訂單按鈕(新增一筆明細)
def add_order():
    if request.method == 'POST':
        cursor.execute("SELECT max(item.id) FROM item inner join order on(order.order_id=item.order_id)")
        rows = cursor.fetchall()
        item_id =rows[0][0]+1



        product_name = request.form.get("product_name")
        cursor.execute("SELECT product.id FROM product WHERE product.name=?",(product_name,))
        rows = cursor.fetchall()
        product_id =rows[0][0]

        size = request.form.get("size")
        ice = request.form.get("ice")
        sugar = request.form.get("sugar")
        temperature = request.form.get("temperature")
        quantity = request.form.get("quantity")

        cursor.execute("INSERT INTO item VALUES (?,?,?,?,?,?,?,?)",(item_id,order_id,product_id,size,ice,sugar,temperature,quantity))
        
    
    return render_template("order_drink.html")




@app.route("/inf_bt",methods=['POST']) #店家查看訂單頁面 inf對應按鈕
def inf_bt():   
    cursor.execute("SELECT order.order_id FROM order")
    rows = cursor.fetchall()
    return render_template("store_check.html",items=rows)

@app.route("/store_check.html")
@app.route("/store_check",methods=['POST']) #店家查看詳細訂單頁面
def store_check():
    print()

@app.route("/admin_order.html")
@app.route("/admin_order",methods=['POST']) #店家查看訂單頁面
def admin_order():
    int_bt = request.form.get("inf_bt")
    if request.method == 'POST': #店家查看細部資訊
        cursor.execute("SELECT order_id FROM order WHERE order_id=?",(int_bt,))
        rows = cursor.fetchall()
        if not rows:
            return render_template("admin_order.html",items=rows)
        
    cursor.execute("SELECT order.order_id,customer.phone,order.status FROM order inner join customer on(customer.customer_id==order.customer_id)")
    rows = cursor.fetchall()
    return render_template("admin_order.html",items=rows)

if __name__ == "__main__":
    app.run(debug=True)

