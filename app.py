from flask import Flask, render_template, request, redirect, session
import pandas as pd
import joblib
import sqlite3

app = Flask(__name__)
app.secret_key = "fraud_secret"

model = joblib.load("fraud_detection_model.pkl")


# Home Landing Page
@app.route("/")
def landing():
    return render_template("landing.html")


# Register Page
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match!", 400

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        # Modern DB Init with Email Support
        cur.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, email TEXT, password TEXT)")
        
        # Check if email column exists (migration)
        cur.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cur.fetchall()]
        if 'email' not in columns:
            cur.execute("ALTER TABLE users ADD COLUMN email TEXT")

        cur.execute("INSERT INTO users (username, email, password) VALUES (?,?,?)",(username, email, password))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# Login Page
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        identifier = request.form["identifier"] # Username or Email
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        # Support login by username or email
        cur.execute("SELECT * FROM users WHERE (username=? OR email=?) AND password=?",(identifier, identifier, password))
        user = cur.fetchone()

        conn.close()

        if user:
            session["user"] = user[0] # Set session to username
            return redirect("/dashboard")

    return render_template("login.html")


# Dashboard
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    return render_template("dashboard.html", user=session["user"])


# Prediction Page
@app.route("/predict", methods=["POST"])
def predict():

    data = [
        int(request.form["Gender"]),
        int(request.form["Age"]),
        int(request.form["State"]),
        int(request.form["City"]),
        int(request.form["Bank_Branch"]),
        int(request.form["Account_Type"]),
        float(request.form["Transaction_Amount"]),
        int(request.form["Merchant_ID"]),
        int(request.form["Transaction_Type"]),
        int(request.form["Merchant_Category"]),
        float(request.form["Account_Balance"]),
        int(request.form["Transaction_Device"]),
        int(request.form["Transaction_Location"]),
        int(request.form["Device_Type"]),
        int(request.form["Currency"]),
        int(request.form["Transaction_Day"]),
        int(request.form["Transaction_Month"]),
        int(request.form["Transaction_Hour"])
    ]

    input_data = pd.DataFrame([data])

    prediction = model.predict(input_data)[0]

    if prediction == 1:
        result = "⚠ Fraudulent Transaction"
    else:
        result = "✅ Legitimate Transaction"

    return render_template("dashboard.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)