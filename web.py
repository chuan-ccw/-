from flask import Flask
import pyodbc

app = Flask(__name__)

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

# ---------- Test DB Function ----------
def test_db_connection():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 5 * FROM customer;")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        return str(e)

# ---------- Flask Routes ----------
@app.route("/")
def home():
    return "DrinkShop Flask is Running on Azure!"

@app.route("/test-db")
def test_db():
    result = test_db_connection()
    return str(result)

# ---------- Main ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
