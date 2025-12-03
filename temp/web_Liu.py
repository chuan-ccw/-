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
@app.route("/customer_login",methods=['GET','POST']) #客人登入介面
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
            cursor.execute("INSERT INTO [order] (customer_id) VALUES (?)",(customer_id,))
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
    

@app.route("/product_name",methods=['GET','POST']) #客人選擇飲料(下拉式選單)
def product_name():    
    cursor.execute("SELECT product.name FROM product")
    rows = cursor.fetchall() 
    return render_template("customer_order.html",items=rows)

@app.route("/store_name",methods=['GET','POST']) #客人選擇店家(下拉式選單)
def store_name():    
    cursor.execute("SELECT store.name FROM store")
    rows = cursor.fetchall() 
    return render_template("customer_order.html",items=rows)

@app.route("/order_drink.html")
@app.route("/order_drink",methods=['GET','POST']) #客人客製化頁面
def order_drink():    
    global store_id
    if request.method == 'POST':
        product_name = request.form.get("product_name")
        cursor.execute("SELECT photo FROM product WHERE name=?",(product_name,))
        store_id = request.form.get("store_id")
        rows = cursor.fetchall() 
        return render_template("order_drink.html",items=rows)


    return render_template("order_drink.html")

@app.route("/add_order",methods=['GET','POST']) #客人按下加入訂單按鈕(新增一筆明細)
def add_order():
    global order_id
    if request.method == 'POST':
        cursor.execute("SELECT max(item.id) FROM item inner join [order] on([order].order_id=item.order_id)")
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
        conn.commit()
    
    return render_template("order_drink.html")


@app.route("/order_summary.html")
@app.route("/order_summary",methods=['GET','POST']) #客人訂單總覽
def order_summary():
    cursor.execute("SELECT sum(item.price) FROM item  WHERE item.order_id=?",(order_id,))
    rows = cursor.fetchall()
    tot_price = rows[0][0]
    cursor.execute("SELECT sum(item.quantity) FROM item inner join product on(item.product_id=product.product_id) WHERE item.order_id=?",(order_id,))
    rows = cursor.fetchall()
    tot_amount = rows[0][0]
    cursor.execute("SELECT product.name,item.size,item.ice,item.sugar,item.temperature,item.quantity FROM item inner join product on(item.product_id=product.product_id) WHERE item.order_id=?",(order_id,))
    rows = cursor.fetchall()

    if request.method == 'POST': #客人結帳按鈕
        cursor.execute("INSERT INTO [order] VALUES (?,?,?,?,?,?)",(order_id,store_id,customer_id,tot_price,tot_amount,"未完成"))
        conn.commit()
        return render_template("order_success.html")

    return render_template("order_summary.html",items=rows)

@app.route("/order_success.html")
@app.route("/order_success",methods=['GET','POST']) #客人訂單成功
def order_success():
    cursor.execute("SELECT sum(item.price) FROM item  WHERE item.order_id=?",(order_id,))
    rows = cursor.fetchall()
    tot_price = rows[0][0]
    cursor.execute("SELECT sum(item.quantity) FROM item inner join product on(item.product_id=product.product_id) WHERE item.order_id=?",(order_id,))
    rows = cursor.fetchall()
    tot_amount = rows[0][0]
    cursor.execute("SELECT product.name,item.size,item.ice,item.sugar,item.temperature,item.quantity FROM item inner join product on(item.product_id=product.product_id) WHERE item.order_id=?",(order_id,))
    

    return render_template("order_summary.html",items=rows,order_id=order_id,store_id=store_id)


@app.route("/inf_bt",methods=['GET','POST']) #店家查看訂單頁面 inf對應按鈕
def inf_bt():   
    cursor.execute("SELECT [order].order_id FROM [order]")
    rows = cursor.fetchall()
    return render_template("store_check.html",items=rows)


@app.route("/admin_order_detail.html")
@app.route("/admin_order_detail",methods=['GET','POST']) #店家查看詳細訂單頁面
def admin_order_detail():
    global order_id
    cursor.execute("SELECT tot_price,item.item_id,item.order_id,item.product_id,item.size,item.ice,item.sugar,item.temperature,item.quantity FROM [order] inner join item on(item.order_id=[order].order_id) WHERE [order].order_id=?",(order_id,))
    rows = cursor.fetchall()
    return  render_template("admin_order_detail.html",items=rows)


@app.route("/admin_order.html")
@app.route("/admin_order",methods=['GET','POST']) #店家查看訂單頁面
def admin_order():
    global order_id
    int_bt = request.form.get("inf_bt")

    if request.method == 'POST': #店家查看細部資訊
        cursor.execute("SELECT order_id FROM [order] WHERE order_id=?",(int(int_bt),))
        rows = cursor.fetchall()
        if not rows:
            return render_template("admin_order.html",items=rows)
        else:
            order_id = rows[0][0]
            return render_template("admin_order_detail.html",items=rows)
        
    cursor.execute("SELECT [order].order_id,customer.phone,[order].status FROM [order] inner join customer on(customer.customer_id=[order].customer_id)")
    rows = cursor.fetchall()
    return render_template("admin_order.html",items=rows)

if __name__ == "__main__":
    app.run(debug=True)
