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
    # cur.execute("SELECT * FROM products")
    # products = cur.fetchall()
    cur.close()
    conn.close()
    
    # return render_template("orders.html", products=products, username=session["user"])
    return render_template("orders.html", username=session["user"])

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)