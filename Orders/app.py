# app.py
import os
import csv
import io
import zipfile
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
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
    
    # Validate stock availability before creating order
    for item in items:
        cur.execute(
            "SELECT stock FROM products WHERE id = %s",
            (item["product_id"],)
        )
        result = cur.fetchone()
        
        if not result:
            cur.close()
            conn.close()
            return {"error": f"Product ID {item['product_id']} not found"}, 400
        
        available_stock = result[0]
        if available_stock <= 0:
            cur.close()
            conn.close()
            return {"error": f"No stock available for product ID {item['product_id']}"}, 400
        
        if available_stock < item["quantity"]:
            cur.close()
            conn.close()
            return {"error": f"Insufficient stock for product ID {item['product_id']}. Available: {available_stock}, Required: {item['quantity']}"}, 400
    
    # Insert order
    cur.execute(
        "INSERT INTO orders (user_id, shop_id, created_at) VALUES (%s, %s, NOW())",
        (session["user_id"], shop_id)
    )
    order_id = cur.lastrowid
    
    # Insert order items and reduce stock
    for item in items:
        cur.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
            (order_id, item["product_id"], item["quantity"], item["price"])
        )
        # Reduce stock after order is created
        cur.execute(
            "UPDATE products SET stock = stock - %s WHERE id = %s",
            (item["quantity"], item["product_id"])
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
    
    return render_template("shops.html", shops=shops_list, username=session["user"], role=session.get("role", "sales"))

@app.route("/api/shops-data")
def get_shops_data():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    search = request.args.get("search", "").lower()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get all shops with all fields including area code
    cur.execute("""
        SELECT s.id, s.name, s.address, s.number_1, s.number_2, s.area_code, ac.area_name as area_name
        FROM shops s
        LEFT JOIN area_code ac ON s.area_code = ac.code
    """)
    shops_list = cur.fetchall()
    
    shops_data = []
    for shop in shops_list:
        shop_id, shop_name, address, number_1, number_2, area_code, area_name = shop
        
        # Apply search filter
        if search and search not in shop_name.lower() and search not in address.lower():
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
            "area_code": area_code,
            "area_name": area_name,
            "number_1": number_1,
            "number_2": number_2,
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
    
    # Get shop info with area code
    cur.execute("""
        SELECT s.id, s.name, s.address, s.number_1, s.number_2, s.area_code, ac.area_name as area_name
        FROM shops s
        LEFT JOIN area_code ac ON s.area_code = ac.code
        WHERE s.id = %s
    """, (shop_id,))
    shop = cur.fetchone()
    
    if not shop:
        cur.close()
        conn.close()
        return {"error": "Shop not found"}, 404
    
    shop_id, shop_name, address, number_1, number_2, area_code, area_name = shop
    
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
            "area_code": area_code,
            "area_name": area_name,
            "number_1": number_1,
            "number_2": number_2,
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

@app.route("/api/create-shop", methods=["POST"])
def create_shop():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Only admin can create shops"}, 403
    
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('address'):
        return {"error": "Shop name and address are required"}, 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        area_code = data.get('area_code') if data.get('area_code') else None
        
        cur.execute("""
            INSERT INTO shops (name, address, area_code, number_1, number_2)
            VALUES (%s, %s, %s, %s, %s)
        """, (data['name'], data['address'], area_code, data.get('number_1', ''), data.get('number_2', '')))
        
        conn.commit()
        shop_id = cur.lastrowid
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Shop created successfully", "shop_id": shop_id}, 201
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/api/update-shop/<int:shop_id>", methods=["PUT"])
def update_shop(shop_id):
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Only admin can edit shops"}, 403
    
    data = request.get_json()
    
    if not data:
        return {"error": "No data provided"}, 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build update query based on provided fields
        update_fields = []
        params = []
        
        if 'name' in data:
            update_fields.append("name = %s")
            params.append(data['name'])
        if 'address' in data:
            update_fields.append("address = %s")
            params.append(data['address'])
        if 'area_code' in data:
            update_fields.append("area_code = %s")
            params.append(data['area_code'] if data['area_code'] else None)
        if 'number_1' in data:
            update_fields.append("number_1 = %s")
            params.append(data['number_1'])
        if 'number_2' in data:
            update_fields.append("number_2 = %s")
            params.append(data['number_2'])
        
        if not update_fields:
            return {"error": "No fields to update"}, 400
        
        params.append(shop_id)
        
        query = f"UPDATE shops SET {', '.join(update_fields)} WHERE id = %s"
        cur.execute(query, params)
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Shop updated successfully"}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/api/area-codes")
def get_area_codes():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT code, area_name FROM area_code ORDER BY code ASC")
    area_codes = cur.fetchall()
    cur.close()
    conn.close()
    
    area_code_list = []
    for code, area_name in area_codes:
        area_code_list.append({
            "code": code,
            "area_name": area_name
        })
    
    return {"area_codes": area_code_list}

@app.route("/api/create-area-code", methods=["POST"])
def create_area_code():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Only admin can create area codes"}, 403
    
    data = request.get_json()
    
    if not data or not data.get('code') or not data.get('area_name'):
        return {"error": "Area code and name are required"}, 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        code = data['code'].strip().upper()
        area_name = data['area_name'].strip()
        
        cur.execute("""
            INSERT INTO area_code (code, area_name)
            VALUES (%s, %s)
        """, (code, area_name))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Area code created successfully"}, 201
    except Exception as e:
        # Check if it's a duplicate key error
        if "Duplicate entry" in str(e):
            return {"error": "Area code already exists"}, 409
        return {"error": str(e)}, 500

@app.route("/api/update-area-code/<code>", methods=["PUT"])
def update_area_code(code):
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Only admin can update area codes"}, 403
    
    data = request.get_json()
    
    if not data or not data.get('area_name'):
        return {"error": "Area name is required"}, 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        area_name = data['area_name'].strip()
        
        cur.execute("""
            UPDATE area_code
            SET area_name = %s
            WHERE code = %s
        """, (area_name, code.upper()))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Area code updated successfully"}
    except Exception as e:
        return {"error": str(e)}, 500

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

@app.route("/api/download-orders")
def download_orders():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Unauthorized"}, 401
    
    date_range = request.args.get('dateRange', 'today')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Determine date range
    today = datetime.now().date()
    
    if date_range == 'today':
        start_date = today
        end_date = today
        range_label = "Today's Orders"
    elif date_range == 'yesterday':
        yesterday = today - timedelta(days=1)
        start_date = yesterday
        end_date = yesterday
        range_label = "Yesterday's Orders"
    elif date_range == 'last7days':
        start_date = today - timedelta(days=7)
        end_date = today
        range_label = "Last 7 Days Orders"
    else:
        start_date = today
        end_date = today
        range_label = "Orders"
    
    # Fetch orders
    cur.execute("""
        SELECT o.id, o.user_id, u.username, o.shop_id, s.name as shop_name, s.address as shop_address , o.created_at
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        LEFT JOIN shops s ON o.shop_id = s.id
        WHERE DATE(o.created_at) >= %s AND DATE(o.created_at) <= %s
        ORDER BY o.created_at DESC
    """, (start_date, end_date))
    
    orders = cur.fetchall()
    
    if not orders:
        cur.close()
        conn.close()
        return "No orders found for this date range", 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
    # Create ZIP file with individual order files
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for order in orders:
            order_id, user_id, username, shop_id, shop_name, shop_address, created_at = order
            
            # Format individual order
            order_content = format_single_order(order_id, shop_name, shop_address, created_at, cur)
            
            # Create filename
            filename = f"Order_{order_id}_{created_at.strftime('%Y%m%d_%H%M%S')}.txt"
            
            # Add file to zip
            zip_file.writestr(filename, order_content)
    
    zip_buffer.seek(0)
    cur.close()
    conn.close()
    
    # Return ZIP file
    zip_filename = f"Orders_{date_range}_{today.strftime('%Y%m%d')}.zip"
    return zip_buffer.getvalue(), 200, {
        'Content-Type': 'application/zip',
        'Content-Disposition': f'attachment; filename="{zip_filename}"'
    }

@app.route("/api/preview-orders")
def preview_orders():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Unauthorized"}, 401
    
    date_range = request.args.get('dateRange', 'today')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Determine date range
    today = datetime.now().date()
    
    if date_range == 'today':
        start_date = today
        end_date = today
    elif date_range == 'yesterday':
        yesterday = today - timedelta(days=1)
        start_date = yesterday
        end_date = yesterday
    elif date_range == 'last7days':
        start_date = today - timedelta(days=7)
        end_date = today
    else:
        start_date = today
        end_date = today
    
    # Fetch first order
    cur.execute("""
        SELECT o.id, o.user_id, u.username, o.shop_id, s.name as shop_name, o.created_at
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        LEFT JOIN shops s ON o.shop_id = s.id
        WHERE DATE(o.created_at) >= %s AND DATE(o.created_at) <= %s
        ORDER BY o.created_at DESC
        LIMIT 1
    """, (start_date, end_date))
    
    order = cur.fetchone()
    
    if not order:
        cur.close()
        conn.close()
        return "No orders found for preview", 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
    order_id, user_id, username, shop_id, shop_name, created_at = order
    preview_content = format_single_order(order_id, username, shop_name, created_at, cur)
    
    cur.close()
    conn.close()
    
    return preview_content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

def format_single_order(order_id, shop_name, shop_address, created_at, cur):
    """Format a single order for dot matrix printer (fixed-width text)"""
    lines = []
    
    # Header
    # lines.append("=" * 80)
    # lines.append("THE TRIANGLE SOLUTIONS - ORDER RECEIPT".center(80))
    # lines.append("=" * 80)
    # lines.append("")
    
    # Order information
    lines.append(f"ORDER #: {order_id}")
    lines.append(f"DATE: {created_at.strftime('%d-%m-%Y %H:%M:%S')}")
    # lines.append(f"SALESMAN: {username}")
    lines.append(f"SHOP: {shop_name}")
    lines.append(f"SHOP ADDRESS: {shop_address}")
    lines.append("")
    lines.append("-" * 80)
    
    # Fetch order items
    cur.execute("""
        SELECT p.name, oi.quantity, oi.price, (oi.quantity * oi.price) as total
        FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = %s
    """, (order_id,))
    
    items = cur.fetchall()
    
    if items:
        # Item header
        lines.append(f"{'PRODUCT':<40} {'QTY':>8} {'PRICE':>12} {'TOTAL':>12}")
        lines.append("-" * 80)
        
        total_amount = 0
        for item in items:
            product_name, quantity, price, item_total = item
            product_name = product_name[:40] if product_name else "Unknown"
            qty_str = f"{quantity}"
            price_str = f"₹{float(price):.2f}"
            total_str = f"₹{float(item_total):.2f}"
            
            lines.append(f"{product_name:<40} {qty_str:>8} {price_str:>12} {total_str:>12}")
            total_amount += float(item_total)
        
        lines.append("-" * 80)
        lines.append(f"{'TOTAL AMOUNT:':<48} {f'₹{total_amount:.2f}':>27}")
    else:
        lines.append("NO ITEMS IN THIS ORDER".center(80))
    
    lines.append("")
    lines.append("-" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}".center(80))
    lines.append("=" * 80)
    lines.append("")
    
    return "\n".join(lines)

def format_orders_text(orders, cur, range_label):
    """Format orders for dot matrix printer (fixed-width text) - LEGACY"""
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append("THE TRIANGLE SOLUTIONS - ORDER REPORT".center(80))
    lines.append(range_label.center(80))
    lines.append("Generated: " + datetime.now().strftime("%d-%m-%Y %H:%M:%S").center(80))
    lines.append("=" * 80)
    lines.append("")
    
    if not orders:
        lines.append("NO ORDERS FOUND FOR THIS DATE RANGE".center(80))
        lines.append("")
    else:
        for order in orders:
            order_id, user_id, username, shop_id, shop_name, created_at = order
            
            # Order header
            lines.append("-" * 80)
            lines.append(f"ORDER #: {order_id:<20} SALESMAN: {username:<20} DATE: {created_at.strftime('%d-%m-%Y %H:%M')}")
            lines.append(f"SHOP: {shop_name}")
            lines.append("")
            
            # Fetch order items
            cur.execute("""
                SELECT p.name, oi.quantity, oi.price, (oi.quantity * oi.price) as total
                FROM order_items oi
                LEFT JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            """, (order_id,))
            
            items = cur.fetchall()
            
            if items:
                # Item header
                lines.append(f"{'PRODUCT':<40} {'QTY':>8} {'PRICE':>12} {'TOTAL':>12}")
                lines.append("-" * 80)
                
                total_amount = 0
                for item in items:
                    product_name, quantity, price, item_total = item
                    product_name = product_name[:40] if product_name else "Unknown"
                    qty_str = f"{quantity}"
                    price_str = f"₹{float(price):.2f}"
                    total_str = f"₹{float(item_total):.2f}"
                    
                    lines.append(f"{product_name:<40} {qty_str:>8} {price_str:>12} {total_str:>12}")
                    total_amount += float(item_total)
                
                lines.append("-" * 80)
                lines.append(f"{'TOTAL AMOUNT:':<48} {f'₹{total_amount:.2f}':>27}")
            
            lines.append("")
            lines.append("")
    
    lines.append("=" * 80)
    lines.append("END OF REPORT".center(80))
    lines.append("=" * 80)
    
    return "\n".join(lines)

@app.route("/api/preview-outstanding")
def preview_outstanding():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Unauthorized"}, 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch outstanding payments grouped by area code
    preview_content = format_outstanding_by_area_code(cur)
    
    cur.close()
    conn.close()
    
    return preview_content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route("/api/download-outstanding")
def download_outstanding():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Unauthorized"}, 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create ZIP file with separate files for each area code
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Fetch outstanding payments grouped by area code
        cur.execute("""
            SELECT DISTINCT COALESCE(ac.code, 'NO_CODE') as area_code,
                   COALESCE(ac.area_name, 'Unassigned') as area_name
            FROM shops s
            LEFT JOIN area_code ac ON s.area_code = ac.code
            LEFT JOIN orders o ON s.id = o.shop_id AND o.payment_status = 'pending'
            LEFT JOIN order_items oi ON o.id = oi.order_id
            GROUP BY COALESCE(ac.code, 'NO_CODE'), COALESCE(ac.area_name, 'Unassigned')
            HAVING SUM(oi.quantity * oi.price) > 0 OR COUNT(DISTINCT o.id) > 0
            ORDER BY COALESCE(ac.code, 'Z')
        """)
        
        area_codes = cur.fetchall()
        
        if not area_codes:
            # Add a file indicating no outstanding payments
            content = "NO OUTSTANDING PAYMENTS FOUND"
            zip_file.writestr("No_Outstanding_Payments.txt", content)
        else:
            for area_code, area_name in area_codes:
                # Format report for each area code
                content = format_outstanding_for_area_code(area_code, area_name, cur)
                filename = f"{area_code}_{area_name.replace(' ', '_')}.txt"
                zip_file.writestr(filename, content)
    
    zip_buffer.seek(0)
    cur.close()
    conn.close()
    
    # Return ZIP file
    zip_filename = f"Outstanding_Payments_ByAreaCode_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    return zip_buffer.getvalue(), 200, {
        'Content-Type': 'application/zip',
        'Content-Disposition': f'attachment; filename="{zip_filename}"'
    }

def format_outstanding_for_area_code(area_code, area_name, cur):
    """Format outstanding payments for a specific area code"""
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append("THE TRIANGLE SOLUTIONS - OUTSTANDING PAYMENTS REPORT".center(80))
    lines.append(f"AREA CODE: {area_code} - {area_name}".center(80))
    lines.append(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}".center(80))
    lines.append("=" * 80)
    lines.append("")
    
    # Fetch outstanding payments for this area code
    cur.execute("""
        SELECT 
            s.id,
            s.name as shop_name,
            s.address,
            s.number_1,
            s.number_2,
            COALESCE(SUM(oi.quantity * oi.price), 0) as outstanding_amount,
            COUNT(DISTINCT o.id) as pending_orders
        FROM shops s
        LEFT JOIN orders o ON s.id = o.shop_id AND o.payment_status = 'pending'
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE COALESCE(s.area_code, 'NO_CODE') = %s OR (s.area_code IS NULL AND %s = 'NO_CODE')
        GROUP BY s.id, s.name, s.address, s.number_1, s.number_2
        HAVING outstanding_amount > 0 OR pending_orders > 0
        ORDER BY s.name
    """, (area_code if area_code != 'NO_CODE' else None, area_code))
    
    results = cur.fetchall()
    
    if not results:
        lines.append("NO OUTSTANDING PAYMENTS FOUND".center(80))
        lines.append("")
    else:
        area_total = 0
        
        for result in results:
            shop_id, shop_name, address, number_1, number_2, outstanding, pending = result
            outstanding = float(outstanding) if outstanding else 0.0
            pending = int(pending) if pending else 0
            
            # Shop details
            lines.append(f"SHOP: {shop_name}")
            if address:
                address_display = address[:70]
                lines.append(f"ADDRESS: {address_display}")
            if number_1:
                lines.append(f"CONTACT 1: {number_1}")
            if number_2:
                lines.append(f"CONTACT 2: {number_2}")
            
            lines.append(f"PENDING ORDERS: {pending}  |  OUTSTANDING: ₹{outstanding:,.2f}")
            lines.append("-" * 80)
            lines.append("")
            
            area_total += outstanding
        
        # Print area total
        lines.append("=" * 80)
        lines.append(f"{'TOTAL - OUTSTANDING PAYMENTS:':.<55} {f'₹{area_total:,.2f}':>23}")
        lines.append("=" * 80)
    
    lines.append("")
    lines.append(f"Page generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    lines.append("=" * 80)
    
    return "\n".join(lines)

def format_outstanding_by_area_code(cur):
    """Format outstanding payments by area code for dot matrix printer"""
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append("THE TRIANGLE SOLUTIONS - OUTSTANDING PAYMENTS REPORT".center(80))
    lines.append(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}".center(80))
    lines.append("=" * 80)
    lines.append("")
    
    # Fetch outstanding payments grouped by area code
    cur.execute("""
        SELECT 
            COALESCE(ac.code, 'NO CODE') as area_code,
            COALESCE(ac.area_name, 'Unassigned') as area_name,
            s.id,
            s.name as shop_name,
            s.address,
            s.number_1,
            s.number_2,
            COALESCE(SUM(oi.quantity * oi.price), 0) as outstanding_amount,
            COUNT(DISTINCT o.id) as pending_orders
        FROM shops s
        LEFT JOIN area_code ac ON s.area_code = ac.code
        LEFT JOIN orders o ON s.id = o.shop_id AND o.payment_status = 'pending'
        LEFT JOIN order_items oi ON o.id = oi.order_id
        GROUP BY s.id, s.name, s.address, s.number_1, s.number_2, ac.code, ac.area_name
        HAVING outstanding_amount > 0 OR pending_orders > 0
        ORDER BY COALESCE(ac.code, 'Z'), s.name
    """)
    
    results = cur.fetchall()
    
    if not results:
        lines.append("NO OUTSTANDING PAYMENTS FOUND".center(80))
        lines.append("")
    else:
        current_area_code = None
        area_total = 0
        grand_total = 0
        
        for result in results:
            area_code, area_name, shop_id, shop_name, address, number_1, number_2, outstanding, pending = result
            area_code = area_code or 'NO CODE'
            area_name = area_name or 'Unassigned'
            outstanding = float(outstanding) if outstanding else 0.0
            pending = int(pending) if pending else 0
            
            # Print area code header when it changes
            if current_area_code != area_code:
                if current_area_code is not None:
                    # Print area total
                    lines.append("-" * 80)
                    lines.append(f"{f'AREA TOTAL ({current_area_code}):':.<55} {f'₹{area_total:,.2f}':>23}")
                    lines.append("")
                
                # New area code section
                lines.append("=" * 80)
                lines.append(f"AREA CODE: {area_code} - {area_name}")
                lines.append("=" * 80)
                lines.append("")
                
                current_area_code = area_code
                area_total = 0
            
            # Shop details
            lines.append(f"SHOP: {shop_name}")
            if address:
                address_display = address[:70]
                lines.append(f"ADDRESS: {address_display}")
            if number_1:
                lines.append(f"CONTACT 1: {number_1}")
            if number_2:
                lines.append(f"CONTACT 2: {number_2}")
            
            lines.append(f"PENDING ORDERS: {pending}  |  OUTSTANDING: ₹{outstanding:,.2f}")
            lines.append("-" * 80)
            lines.append("")
            
            area_total += outstanding
            grand_total += outstanding
        
        # Print last area total
        if current_area_code is not None:
            lines.append("-" * 80)
            lines.append(f"{f'AREA TOTAL ({current_area_code}):':.<55} {f'₹{area_total:,.2f}':>23}")
            lines.append("")
        
        # Grand totals
        lines.append("=" * 80)
        lines.append(f"{'GRAND TOTAL - ALL OUTSTANDING PAYMENTS:':.<55} {f'₹{grand_total:,.2f}':>23}")
        lines.append("=" * 80)
    
    lines.append("")
    lines.append(f"Page generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    lines.append("=" * 80)
    
    return "\n".join(lines)

# def format_orders_csv(orders, cur, range_label):
#     """Format orders as CSV for Excel"""
#     output = io.StringIO()
#     writer = csv.writer(output)
    
#     # Headers
#     writer.writerow(['Report', range_label, '', '', ''])
#     writer.writerow(['Generated', datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '', '', ''])
#     writer.writerow([])
#     writer.writerow(['Order ID', 'Salesman', 'Shop', 'Date', 'Product', 'Quantity', 'Price', 'Total'])
    
#     if orders:
#         for order in orders:
#             order_id, user_id, username, shop_id, shop_name, created_at = order
            
#             # Fetch order items
#             cur.execute("""
#                 SELECT p.name, oi.quantity, oi.price, (oi.quantity * oi.price) as total
#                 FROM order_items oi
#                 LEFT JOIN products p ON oi.product_id = p.id
#                 WHERE oi.order_id = %s
#             """, (order_id,))
            
#             items = cur.fetchall()
            
#             if items:
#                 for idx, item in enumerate(items):
#                     product_name, quantity, price, item_total = item
#                     if idx == 0:
#                         writer.writerow([
#                             order_id,
#                             username,
#                             shop_name,
#                             created_at.strftime("%d-%m-%Y %H:%M"),
#                             product_name,
#                             quantity,
#                             float(price),
#                             float(item_total)
#                         ])
#                     else:
#                         writer.writerow([
#                             '',
#                             '',
#                             '',
#                             '',
#                             product_name,
#                             quantity,
#                             float(price),
#                             float(item_total)
#                         ])
#             else:
#                 writer.writerow([
#                     order_id,
#                     username,
#                     shop_name,
#                     created_at.strftime("%d-%m-%Y %H:%M"),
#                     'No items',
#                     '',
#                     '',
#                     ''
#                 ])
    
#     return output.getvalue()

# ==================== PRODUCTS MANAGEMENT ====================

@app.route("/products")
def products():
    if "user" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") != "admin":
        return redirect(url_for("orders"))
    
    return render_template("products.html", username=session["user"], role=session.get("role", "sales"))

@app.route("/api/products")
def get_products_list():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, name, stock, mrp, price, created_at, updated_at
        FROM products
        ORDER BY name ASC
    """)
    
    products = cur.fetchall()
    cur.close()
    conn.close()
    
    product_list = []
    for product in products:
        product_list.append({
            "id": product[0],
            "name": product[1],
            "stock": int(product[2]),
            "mrp": float(product[3]),
            "price": float(product[4]),
            "created_at": product[5].isoformat() if product[5] else None,
            "updated_at": product[6].isoformat() if product[6] else None
        })
    
    return {"products": product_list}

@app.route("/api/create-product", methods=["POST"])
def create_product():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Only admin can create products"}, 403
    
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('stock') or not data.get('mrp') or not data.get('price'):
        return {"error": "All fields are required"}, 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO products (name, stock, mrp, price, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (data['name'], int(data['stock']), float(data['mrp']), float(data['price'])))
        
        conn.commit()
        product_id = cur.lastrowid
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Product created successfully", "product_id": product_id}, 201
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/api/update-product/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Only admin can edit products"}, 403
    
    data = request.get_json()
    
    if not data:
        return {"error": "No data provided"}, 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        update_fields = []
        params = []
        
        if 'name' in data:
            update_fields.append("name = %s")
            params.append(data['name'])
        if 'stock' in data:
            update_fields.append("stock = %s")
            params.append(int(data['stock']))
        if 'mrp' in data:
            update_fields.append("mrp = %s")
            params.append(float(data['mrp']))
        if 'price' in data:
            update_fields.append("price = %s")
            params.append(float(data['price']))
        
        if not update_fields:
            return {"error": "No fields to update"}, 400
        
        update_fields.append("updated_at = NOW()")
        params.append(product_id)
        
        query = f"UPDATE products SET {', '.join(update_fields)} WHERE id = %s"
        cur.execute(query, params)
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Product updated successfully"}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/api/delete-product/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Only admin can delete products"}, 403
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Product deleted successfully"}
    except Exception as e:
        return {"error": str(e)}, 500

# ==================== PURCHASES/INVENTORY MANAGEMENT ====================

@app.route("/purchases")
def purchases():
    if "user" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") != "admin":
        return redirect(url_for("orders"))
    
    return render_template("purchases.html", username=session["user"], role=session.get("role", "sales"))

@app.route("/api/purchases")
def get_purchases_list():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Only admin can view purchases"}, 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT p.id, p.product_id, pr.name as product_name, p.quantity, p.cost_per_unit, 
               (p.quantity * p.cost_per_unit) as total_cost, p.purchase_date, p.notes
        FROM purchases p
        JOIN products pr ON p.product_id = pr.id
        ORDER BY p.purchase_date DESC
    """)
    
    purchases = cur.fetchall()
    cur.close()
    conn.close()
    
    purchase_list = []
    for purchase in purchases:
        purchase_list.append({
            "id": purchase[0],
            "product_id": purchase[1],
            "product_name": purchase[2],
            "quantity": int(purchase[3]),
            "cost_per_unit": float(purchase[4]),
            "total_cost": float(purchase[5]),
            "purchase_date": purchase[6].isoformat() if purchase[6] else None,
            "notes": purchase[7]
        })
    
    return {"purchases": purchase_list}

@app.route("/api/create-purchase", methods=["POST"])
def create_purchase():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Only admin can create purchases"}, 403
    
    data = request.get_json()
    
    if not data or not data.get('product_id') or not data.get('quantity') or not data.get('cost_per_unit'):
        return {"error": "product_id, quantity, and cost_per_unit are required"}, 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verify product exists
        cur.execute("SELECT id FROM products WHERE id = %s", (data['product_id'],))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return {"error": "Product not found"}, 404
        
        # Insert purchase record
        cur.execute("""
            INSERT INTO purchases (product_id, quantity, cost_per_unit, purchase_date, notes)
            VALUES (%s, %s, %s, NOW(), %s)
        """, (data['product_id'], int(data['quantity']), float(data['cost_per_unit']), data.get('notes', '')))
        
        purchase_id = cur.lastrowid
        
        # Update product stock
        cur.execute(
            "UPDATE products SET stock = stock + %s WHERE id = %s",
            (int(data['quantity']), data['product_id'])
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Purchase recorded successfully", "purchase_id": purchase_id}, 201
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/api/update-purchase/<int:purchase_id>", methods=["PUT"])
def update_purchase(purchase_id):
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Only admin can edit purchases"}, 403
    
    data = request.get_json()
    
    if not data:
        return {"error": "No data provided"}, 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get current purchase details
        cur.execute(
            "SELECT product_id, quantity FROM purchases WHERE id = %s",
            (purchase_id,)
        )
        result = cur.fetchone()
        
        if not result:
            cur.close()
            conn.close()
            return {"error": "Purchase not found"}, 404
        
        old_quantity = result[1]
        new_quantity = int(data.get('quantity', old_quantity))
        
        # If quantity changed, update product stock
        if 'quantity' in data:
            quantity_diff = new_quantity - old_quantity
            cur.execute(
                "UPDATE products SET stock = stock + %s WHERE id = %s",
                (quantity_diff, result[0])
            )
        
        # Update purchase record
        update_fields = []
        params = []
        
        if 'quantity' in data:
            update_fields.append("quantity = %s")
            params.append(int(data['quantity']))
        if 'cost_per_unit' in data:
            update_fields.append("cost_per_unit = %s")
            params.append(float(data['cost_per_unit']))
        if 'notes' in data:
            update_fields.append("notes = %s")
            params.append(data['notes'])
        
        if not update_fields:
            cur.close()
            conn.close()
            return {"error": "No fields to update"}, 400
        
        params.append(purchase_id)
        query = f"UPDATE purchases SET {', '.join(update_fields)} WHERE id = %s"
        cur.execute(query, params)
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Purchase updated successfully"}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/api/delete-purchase/<int:purchase_id>", methods=["DELETE"])
def delete_purchase(purchase_id):
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    if session.get("role") != "admin":
        return {"error": "Only admin can delete purchases"}, 403
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get purchase details to refund stock
        cur.execute(
            "SELECT product_id, quantity FROM purchases WHERE id = %s",
            (purchase_id,)
        )
        result = cur.fetchone()
        
        if not result:
            cur.close()
            conn.close()
            return {"error": "Purchase not found"}, 404
        
        # Reduce product stock by the purchased quantity
        cur.execute(
            "UPDATE products SET stock = stock - %s WHERE id = %s",
            (result[1], result[0])
        )
        
        # Delete purchase record
        cur.execute("DELETE FROM purchases WHERE id = %s", (purchase_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Purchase deleted successfully"}
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True)