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
            session["role"] = user[4]  # Store user role in session
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

@app.route("/past-orders")
def past_orders():
    if "user" not in session:
        return redirect(url_for("login"))
    
    return render_template("past_orders.html", username=session["user"], role=session.get("role", "sales"))

@app.route("/edit-order/<int:order_id>")
def edit_order(order_id):
    if "user" not in session:
        return redirect(url_for("login"))
    
    # Check if user is admin - only admin can edit orders
    if session.get("role") != "admin":
        return redirect(url_for("past_orders"))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify order exists
    cur.execute("SELECT user_id, shop_id FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()
    
    if not order:
        cur.close()
        conn.close()
        return redirect(url_for("past_orders"))
    
    shop_id = order[1]
    
    # Get all shops
    cur.execute("SELECT * FROM shops")
    shops = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template("edit_order.html", order_id=order_id, shops=shops, username=session["user"], role=session.get("role", "sales"))

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

@app.route("/api/get-order/<int:order_id>")
def get_order(order_id):
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get order details
    if session.get("role") == "admin":
        # Admin can access any order
        cur.execute("""
            SELECT o.id, o.shop_id, s.name, o.created_at 
            FROM orders o
            JOIN shops s ON o.shop_id = s.id
            WHERE o.id = %s
        """, (order_id,))
    else:
        cur.execute("""
            SELECT o.id, o.shop_id, s.name, o.created_at 
            FROM orders o
            JOIN shops s ON o.shop_id = s.id
            WHERE o.id = %s AND o.user_id = %s
        """, (order_id, session["user_id"]))
    
    order = cur.fetchone()
    
    if not order:
        cur.close()
        conn.close()
        return {"error": "Order not found"}, 404
    
    order_id, shop_id, shop_name, created_at = order
    
    # Get order items
    cur.execute("""
        SELECT oi.order_id, oi.product_id, p.name, oi.quantity, oi.price
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = %s
    """, (order_id,))
    
    items = cur.fetchall()
    item_list = []
    total_price = 0
    
    for item in items:
        item_id, product_id, product_name, quantity, price = item
        item_total = quantity * price
        total_price += item_total
        item_list.append({
            "id": item_id,
            "product_id": product_id,
            "product_name": product_name,
            "quantity": quantity,
            "price": float(price),
            "total": float(item_total)
        })
    
    cur.close()
    conn.close()
    
    return {
        "id": order_id,
        "shop_id": shop_id,
        "shop_name": shop_name,
        "created_at": created_at.isoformat(),
        "items": item_list,
        "total": float(total_price)
    }

@app.route("/api/past-orders")
def get_past_orders():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    search = request.args.get("search", "").lower()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get orders for the current user
    if session.get("role") == "admin":
        # Admin can see all orders
        cur.execute("""
            SELECT o.id, o.shop_id, s.name, o.created_at 
            FROM orders o
            JOIN shops s ON o.shop_id = s.id
            ORDER BY o.created_at DESC
        """)
    else:
        cur.execute("""
            SELECT o.id, o.shop_id, s.name, o.created_at 
            FROM orders o
            JOIN shops s ON o.shop_id = s.id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
        """, (session["user_id"],))
        
    orders = cur.fetchall()
    order_list = []
    
    for order in orders:
        order_id, shop_id, shop_name, created_at = order
        
        # Get order items
        cur.execute("""
            SELECT oi.order_id, oi.product_id, p.name, oi.quantity, oi.price
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (order_id,))
        
        items = cur.fetchall()
        item_list = []
        total_price = 0
        
        for item in items:
            item_id, product_id, product_name, quantity, price = item
            item_total = quantity * price
            total_price += item_total
            item_list.append({
                "id": item_id,
                "product_id": product_id,
                "product_name": product_name,
                "quantity": quantity,
                "price": float(price),
                "total": float(item_total)
            })
        
        # Apply search filter
        if search and search not in shop_name.lower():
            continue
        
        order_list.append({
            "id": order_id,
            "shop_id": shop_id,
            "shop_name": shop_name,
            "created_at": created_at.isoformat(),
            "items": item_list,
            "total": float(total_price)
        })
    
    cur.close()
    conn.close()
    
    return {"orders": order_list}

@app.route("/api/delete-order/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    if session.get("role") != "admin":
        return {"error": "Only admin users can delete orders"}, 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if order exists
    cur.execute("SELECT user_id FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()
    
    if not order:
        cur.close()
        conn.close()
        return {"error": "Order not found"}, 404
    if order[0] != session["user_id"] and session.get("role") != "admin":
        cur.close()
        conn.close()
        return {"error": "Unauthorized"}, 401
    
    # Delete order items first
    cur.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
    
    # Delete order
    cur.execute("DELETE FROM orders WHERE id = %s", (order_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {"success": True}

@app.route("/api/update-order/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    data = request.json
    items = data.get("items", [])
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if order belongs to current user
    cur.execute("SELECT user_id FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()
    
    if not order:
        cur.close()
        conn.close()
        return {"error": "Order not found"}, 404
    if order[0] != session["user_id"] and session.get("role") != "admin":
        cur.close()        
        conn.close()
        return {"error": "Unauthorized"}, 401
    
    # Delete existing order items
    cur.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
    
    # Insert updated order items
    for item in items:
        cur.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
            (order_id, item["product_id"], item["quantity"], item["price"])
        )
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {"success": True}

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

@app.route("/shops")
def shops():
    if "user" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM shops")
    shops_list = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template("shops.html", shops=shops_list, username=session["user"])

@app.route("/api/shops-data")
def get_shops_data():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    search = request.args.get("search", "").lower()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get all shops
    cur.execute("SELECT id, name, address FROM shops")
    shops_list = cur.fetchall()
    
    shops_data = []
    for shop in shops_list:
        shop_id, shop_name, address = shop
        
        # Apply search filter
        if search and search not in shop_name.lower() and search not in location.lower():
            continue
        
        # Calculate outstanding payment (unpaid orders)
        cur.execute("""
            SELECT COALESCE(SUM(
                (SELECT COALESCE(SUM(oi.quantity * oi.price), 0) 
                 FROM order_items oi 
                 WHERE oi.order_id = o.id)
            ), 0)
            FROM orders o
            WHERE o.shop_id = %s AND o.payment_status = 'pending'
        """, (shop_id,))
        
        outstanding = cur.fetchone()[0]
        outstanding = float(outstanding) if outstanding else 0.0
        
        # Get previous orders count
        cur.execute("""
            SELECT COUNT(*) FROM orders 
            WHERE shop_id = %s AND payment_status = 'collected'
        """, (shop_id,))
        
        paid_orders_count = cur.fetchone()[0]
        
        shops_data.append({
            "id": shop_id,
            "name": shop_name,
            "address": address,
            "outstanding": outstanding,
            "paid_orders_count": paid_orders_count
        })
    
    cur.close()
    conn.close()
    
    return {"shops": shops_data}

@app.route("/api/shop-details/<int:shop_id>")
def get_shop_details(shop_id):
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get shop info
    cur.execute("SELECT id, name, address FROM shops WHERE id = %s", (shop_id,))
    shop = cur.fetchone()
    
    if not shop:
        cur.close()
        conn.close()
        return {"error": "Shop not found"}, 404
    
    shop_id, shop_name, address = shop
    
    # Get pending orders
    cur.execute("""
        SELECT o.id, o.created_at,
        (SELECT COALESCE(SUM(oi.quantity * oi.price), 0) 
         FROM order_items oi 
         WHERE oi.order_id = o.id) as total
        FROM orders o
        WHERE o.shop_id = %s AND o.payment_status = 'pending'
        ORDER BY o.created_at DESC
    """, (shop_id,))
    
    pending_orders = cur.fetchall()
    pending_list = []
    total_outstanding = 0
    
    for order in pending_orders:
        order_id, created_at, total = order
        total = float(total) if total else 0.0
        total_outstanding += total
        pending_list.append({
            "id": order_id,
            "created_at": created_at.isoformat(),
            "total": total
        })
    
    # Get collected payment history (last 10)
    cur.execute("""
        SELECT o.id, o.created_at, o.payment_collected_at,
        (SELECT COALESCE(SUM(oi.quantity * oi.price), 0) 
         FROM order_items oi 
         WHERE oi.order_id = o.id) as total
        FROM orders o
        WHERE o.shop_id = %s AND o.payment_status = 'collected'
        ORDER BY o.payment_collected_at DESC
        LIMIT 10
    """, (shop_id,))
    
    collected_orders = cur.fetchall()
    collected_list = []
    
    for order in collected_orders:
        order_id, created_at, collected_at, total = order
        total = float(total) if total else 0.0
        collected_list.append({
            "id": order_id,
            "created_at": created_at.isoformat(),
            "collected_at": collected_at.isoformat() if collected_at else None,
            "total": total
        })
    
    cur.close()
    conn.close()
    
    return {
        "shop": {
            "id": shop_id,
            "name": shop_name,
            "address": address,
        },
        "pending_orders": pending_list,
        "collected_orders": collected_list,
        "total_outstanding": total_outstanding
    }

@app.route("/api/collect-payment/<int:order_id>", methods=["PUT"])
def collect_payment(order_id):
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify order exists
    cur.execute("SELECT id FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()
    
    if not order:
        cur.close()
        conn.close()
        return {"error": "Order not found"}, 404
    
    # Update payment status
    cur.execute("""
        UPDATE orders 
        SET payment_status = 'collected', payment_collected_at = NOW()
        WHERE id = %s
    """, (order_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {"success": True, "message": "Payment collected successfully"}

@app.route("/save_orders")
def save_orders():
    if "user" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") != "admin":
        return redirect(url_for("past_orders"))

    return render_template("save_orders.html", username=session["user"], role=session.get("role", "sales"))

@app.route("/sales")
def sales():
    if "user" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") != "admin":
        return redirect(url_for("orders"))
    
    return render_template("sales.html", username=session["user"], role=session.get("role", "sales"))

@app.route("/api/salesman-sales")
def get_salesman_sales():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Unauthorized"}, 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get sales by each salesman for current month
    cur.execute("""
        SELECT u.id, u.username, COUNT(o.id) as total_orders, 
               COALESCE(SUM(oi.quantity * oi.price), 0) as total_sales
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id 
            AND YEAR(o.created_at) = YEAR(CURDATE())
            AND MONTH(o.created_at) = MONTH(CURDATE())
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE u.role = 'sales'
        GROUP BY u.id, u.username
        ORDER BY total_sales DESC
    """)
    sales_data = cur.fetchall()
    cur.close()
    conn.close()
    
    salesman_list = []
    for row in sales_data:
        salesman_list.append({
            "id": row[0],
            "username": row[1],
            "total_orders": row[2] if row[2] else 0,
            "total_sales": float(row[3]) if row[3] else 0.0
        })
    
    return {"salesmen": salesman_list}

@app.route("/api/product-sales")
def get_product_sales():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Unauthorized"}, 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get product sales for current month
    cur.execute("""
        SELECT p.id, p.name, 
               SUM(oi.quantity) as total_quantity,
               COALESCE(SUM(oi.quantity * oi.price), 0) as total_revenue
        FROM products p
        LEFT JOIN order_items oi ON p.id = oi.product_id
        LEFT JOIN orders o ON oi.order_id = o.id
            AND YEAR(o.created_at) = YEAR(CURDATE())
            AND MONTH(o.created_at) = MONTH(CURDATE())
        GROUP BY p.id, p.name
        ORDER BY total_revenue DESC
    """)
    product_data = cur.fetchall()
    cur.close()
    conn.close()
    
    product_list = []
    for row in product_data:
        product_list.append({
            "id": row[0],
            "name": row[1],
            "total_quantity": float(row[2]) if row[2] else 0.0,
            "total_revenue": float(row[3]) if row[3] else 0.0
        })
    
    return {"products": product_list}

@app.route("/logout")
def logout():
    session.clear()
    # Also clear the session cookie by setting it to an empty value and expiring it
    response = redirect(url_for("login"))
    response.set_cookie('session', '', expires=0)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)