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

@app.route("/")
def first():        
    return render_template("first.html")

@app.route("/choice_identity",methods=['GET','POST']) #選擇是店家要登入還是客人
def choice_identity():
    if request.method == 'POST':
        button = request.form.get("choice")

        if button == "customer_entry":
            return render_template("customer_login.html")
        elif button == "store_entry":
            return render_template("store_login.html")
        
    return render_template("first.html")

@app.route("/login_customer",methods=['POST']) #客人登入介面
def login_customer():    
    if request.method == 'POST':
        phone = request.form.get("phone")

        cursor.execute("SELECT phone FROM customer WHERE phone==?",(phone,))
        rows = cursor.fetchall()

        if not rows :
            return "customer電話錯誤"
        else:
            return render_template("customer_order.html")
            
    return render_template("customer_login.html")
    
@app.route("/login_store",methods=['GET','POST']) #店家登入介面
def login_store():    
    if request.method == 'POST':
        store_id = request.form.get("store_id")

        cursor.execute("SELECT store_id FROM store WHERE store_id==?",(store_id,))
        rows = cursor.fetchall()

        if not rows :
            return "store id錯誤"
        else:
            return render_template("store_check.html")
            
    return render_template("store_login.html")
    

@app.route("/product_name",methods=['POST']) #客人選擇飲料(下拉式選單)
def product_name():    
    cursor.execute("SELECT product.name FROM product")
    rows = cursor.fetchall() 
    return render_template("customer_order.html",items=rows)

@app.route("/customer_order",methods=['POST']) #客人客製化頁面
def customer_order():    
    if request.method == 'POST':
        product_name = request.form.get("product_name")
        cursor.execute("SELECT photo FROM product WHERE name=?",(product_name,))
        rows = cursor.fetchall() 
        return render_template("customer_order.html",items=rows)


    return render_template("customer_order.html")

@app.route("/inf_bt",methods=['POST']) #店家查看訂單頁面 inf對應按鈕
def inf_bt():   
    cursor.execute("SELECT order.order_id FROM order")
    rows = cursor.fetchall()
    return render_template("store_check.html",items=rows)

@app.route("/store_check",methods=['POST']) #店家查看訂單頁面
def store_check():
    int_bt = request.form.get("inf_bt")
    if request.method == 'POST': #店家查看細部資訊
        cursor.execute("SELECT order_id FROM order WHERE order_id=?",(int_bt,))
        rows = cursor.fetchall()
        if not rows:
            return render_template("store_check.html",items=rows)
        
    cursor.execute("SELECT order.order_id,customer.phone,order.status FROM order inner join customer on(customer.customer_id==order.customer_id)")
    rows = cursor.fetchall()
    return render_template("store_check.html",items=rows)

if __name__ == "__main__":
    app.run(debug=True)

