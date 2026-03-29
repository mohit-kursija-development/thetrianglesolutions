# app.py
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import timedelta
import mysql.connector
from mysql.connector import pooling
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = "secretkey"

# Session configuration for 24-hour persistence
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Create connection pool
db_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DB")
)

def get_db_connection():
    return db_pool.get_connection()

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("orders"))
    return redirect(url_for("login"))

# @app.route("/register", methods=["GET","POST"])
# def register():
#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]

#         hashed_password = generate_password_hash(password)

#         conn = get_db_connection()
#         cur = conn.cursor()
#         cur.execute("INSERT INTO users (username,password) VALUES (%s,%s)", (username,hashed_password))
#         conn.commit()
#         cur.close()
#         conn.close()

#         return redirect(url_for("login"))

#     return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        # Make password string
        password = request.form["password"].strip()  # Remove leading/trailing whitespace

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s",(username,))
        user = cur.fetchone()
        # print(user)
        cur.close()
        conn.close()

        if user and check_password_hash(user[3], password):
            session.permanent = True
            session["user"] = username
            session["user_id"] = user[0]  # Store user ID in session
            return redirect(url_for("orders"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

@app.route("/orders")
def orders():
    if "user" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM shops")
    shops = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template("orders.html", shops=shops, username=session["user"])

@app.route("/api/products")
def get_products():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    conn.close()
    
    product_list = []
    for product in products:
        product_list.append({
            "id": product[0],
            "name": product[1],
            "mrp": float(product[2]),
            "price": product[3] if len(product) > 3 else "",
        })
    
    return {"products": product_list}

@app.route("/api/create-order", methods=["POST"])
def create_order():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    data = request.json
    items = data.get("items", [])
    shop_id = data.get("shop_id")
    
    if not items or not shop_id:
        return {"error": "Invalid order data"}, 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Insert order
    cur.execute(
        "INSERT INTO orders (user_id, shop_id, created_at) VALUES (%s, %s, NOW())",
        (session["user_id"], shop_id)
    )
    order_id = cur.lastrowid
    
    # Insert order items
    for item in items:
        cur.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
            (order_id, item["product_id"], item["quantity"], item["price"])
        )
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {"success": True, "order_id": order_id}

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)