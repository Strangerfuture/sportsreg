import os
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
import requests
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db
# from helpers import login_required

app = Flask(__name__)

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connection to database
db = get_db()

TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY")

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    sports = db.execute("SELECT id, name FROM sports").rows  # your sports from DB

    if request.method == "POST":
        # Collect form data
        full_name = request.form.get("full_name")
        roll_number = request.form.get("roll_number")
        email = request.form.get("email")
        department = request.form.get("department")
        semester = request.form.get("semester")
        selected_sports = request.form.getlist("sports")# multiple sports
        student_id  = department + roll_number + "sem" + semester
        
        # Get CAPTCHA token
        token = request.form.get("cf-turnstile-response")

        # Verify CAPTCHA with Cloudflare
        captcha_data = {
            "secret": TURNSTILE_SECRET_KEY,
            "response": token,
            "remoteip": request.remote_addr
        }
        captcha_result = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data=captcha_data
        ).json()

        if not captcha_result.get("success"):
            return "CAPTCHA failed. Please try again.", 400

        # Save student to DB
        student_id_db = db.execute(
        "INSERT INTO students (full_name, roll_number, email, student_id, department, semester) VALUES (?, ?, ?, ?, ?, ?)",
        [full_name, roll_number, email, student_id, department, semester]
        ).last_insert_rowid

        # Save registrations
        for sport_id in selected_sports:
            db.execute(
                "INSERT INTO registrations (student_id, sport_id) VALUES (?, ?)",
                [student_id_db, sport_id]
            )

        # Redirect to success page with student name
        return  render_template("success.html", full_name=full_name)

    return render_template("index.html", sports=sports, turnstile_site_key=os.getenv("TURNSTILE_SITE_KEY"))


@app.route("/dashboard", methods = ["POST", "GET"])
# @login_required
def dashboard():
    return render_template("dashboard.html")





