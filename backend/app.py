from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import pandas as pd
import math
import pickle

# Load model
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

print("Model Loaded Successfully!")

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app, supports_credentials=True)

app.secret_key = "supersecretkey123"  # change later

# ---------------------------
# Initialize user database
# ---------------------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# ---------------------------
# SIGNUP API
# ---------------------------
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "All fields required"}), 400

    hashed_pw = generate_password_hash(password)

    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                  (name, email, hashed_pw))
        conn.commit()
        conn.close()
        return jsonify({"message": "Signup successful"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400


# ---------------------------
# LOGIN API
# ---------------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, name, email, password FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 400

    user_id, name, email, hashed_pw = user

    if not check_password_hash(hashed_pw, password):
        return jsonify({"error": "Incorrect password"}), 400

    session["user_id"] = user_id
    session["user_name"] = name

    return jsonify({
        "message": "Login successful",
        "name": name
    })


# ---------------------------
# LOGOUT
# ---------------------------
@app.route('/logout')
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


# ---------------------------
# Serve frontend pages
# ---------------------------
@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'login.html')


@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        return send_from_directory(app.static_folder, 'login.html')
    return send_from_directory(app.static_folder, 'dashboard.html')


# ---------------------------
# Your existing prediction APIs below ↓
# ---------------------------

def compute_risk(features: dict):
    loan_amount = float(features.get('loan_amount', 0))
    monthly_income = float(features.get('monthly_income', 1)) or 1
    interest_rate = float(features.get('interest_rate', 0))
    age = float(features.get('age', 40))
    purpose = str(features.get('loan_purpose', '')).lower()
    credit_score = float(features.get('credit_score', 600))
    active_loans = float(features.get('active_loans_count', 0))
    past_due_days = float(features.get('past_due_days', 0))

    dti = loan_amount / (monthly_income + 1)

    score = 0.0
    score += 0.6 * (dti / (dti + 1))
    score += 0.15 * (interest_rate / 100)
    score += 0.1 * (max(0, (60 - credit_score) / 100))
    score += 0.05 * min(active_loans / 10, 1)
    score += 0.1 * math.tanh(past_due_days / 30)

    if age < 22 or age > 65:
        score *= 1.08

    if any(p in purpose for p in ['business', 'investment', 'start', 'medical']):
        score *= 1.05

    prob = max(0.0, min(1.0, score))

    if prob < 0.25:
        action = 'Low risk — Standard reminder & monitor.'
    elif prob < 0.6:
        action = 'Medium risk — Friendly outreach, payment plan offer, increase monitoring.'
    else:
        action = 'High risk — Escalate to recovery team, consider strict follow-up and legal options.'

    explanation = {
        'dti': round(dti, 3),
        'interest_rate': interest_rate,
        'credit_score': credit_score,
        'active_loans_count': active_loans,
        'past_due_days': past_due_days,
    }

    return {
        'probability': round(prob, 4),
        'action': action,
        'explanation': explanation
    }


@app.route('/predict', methods=['POST'])
def predict():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    result = compute_risk(data)

    return jsonify({
        "borrower_id": data.get("borrower_id"),
        "result": result
    })


@app.route('/batch_predict', methods=['POST'])
def batch_predict():
    try:
        file = request.files['file']
        df = pd.read_csv(file)

        # Ensure model is loaded
        global model

        # Predict
        predictions = model.predict(df)

        df['default_probability'] = predictions
        return jsonify({"status": "success", "data": df.to_dict(orient='records')})

    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
