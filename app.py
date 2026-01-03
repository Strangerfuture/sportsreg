import os
import sqlite3
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_file
from flask_session import Session
import pdfkit
import requests
from io import BytesIO
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required

app = Flask(__name__)

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connection to database
# 
def get_db():
    conn = sqlite3.connect("sport.db")
    conn.row_factory = sqlite3.Row
    return conn


TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY")

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    db = get_db()
    cursor = db.cursor()
    # sports = ["Football", "Cricket", "Table Tennis", "Carrom Board", "Chess", "Badminton"]
    sports = cursor.execute("""SELECT id, name FROM sports""")  # your sports from DB
    sports = cursor.fetchall()

    if request.method == "POST":
        # Collect form data
        full_name = request.form.get("full_name")
        roll_number = request.form.get("roll_number")
        email = request.form.get("email")
        gender = request.form.get("gender")
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
        cursor.execute(
        """
        INSERT INTO students
        (full_name, roll_number, gender, email, student_id, department, semester)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (full_name, roll_number, gender, email, student_id, department, semester)
        )
        student_id_db = cursor.lastrowid

        # Save registrations
        for sport_id in selected_sports:
            cursor.execute(
                """INSERT INTO registrations (student_id, sport_id) VALUES (?, ?)""",
                (student_id_db, sport_id)
            )

        db.commit()
        db.close()
        # Redirect to success page with student name
        return  render_template("success.html", full_name=full_name)

    db.close()
    return render_template("index.html", sports=sports, turnstile_site_key=os.getenv("TURNSTILE_SITE_KEY"))




@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        db = get_db()
        cursor = db.cursor()
        user = cursor.execute("SELECT * FROM admins WHERE username = ?",
        (request.form.get("username"),)).fetchone()
        db.close()

        if not user or not check_password_hash(user["password_hash"], request.form.get("password")):
            return render_template("login.html", error="Invalid username or password")

        session["user_id"] = user["id"]
        return redirect("/dashboard")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")




@app.route("/dashboard", methods = ["POST", "GET"])
@login_required
def dashboard():
    db = get_db()
    cur = db.cursor()

    # Get students with their sport and gender
    cur.execute("""
        SELECT st.full_name, st.roll_number, st.email, st.department, st.semester, st.gender, sp.name as sport
        FROM students st
        LEFT JOIN registrations r ON st.id = r.student_id
        LEFT JOIN sports sp ON r.sport_id = sp.id
    """)
    students = cur.fetchall()

    # For filters
    cur.execute("SELECT DISTINCT department FROM students WHERE department IS NOT NULL")
    departments = [row['department'] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT semester FROM students WHERE semester IS NOT NULL")
    semesters = [row['semester'] for row in cur.fetchall()]
    semesters.sort()
    cur.execute("SELECT name FROM sports")
    sports = [row['name'] for row in cur.fetchall()]

    # Gender options
    cur.execute("SELECT DISTINCT gender FROM students WHERE gender IS NOT NULL")
    genders = [row['gender'] for row in cur.fetchall()]

    # Counts for charts
    students_count = []
    for dept in departments:
        cur.execute("SELECT COUNT(*) as count FROM students WHERE department = ?", (dept,))
        students_count.append(cur.fetchone()['count'])

    registrations_count = []
    for sport in sports:
        cur.execute("""
            SELECT COUNT(r.id) as count
            FROM registrations r
            JOIN sports s ON r.sport_id = s.id
            WHERE s.name = ?
        """, (sport,))
        registrations_count.append(cur.fetchone()['count'])

    # Gender counts
    gender_counts = {'Male':0, 'Female':0, 'Other':0}
    for g in gender_counts.keys():
        cur.execute("SELECT COUNT(*) as count FROM students WHERE gender = ?", (g,))
        gender_counts[g] = cur.fetchone()['count']

    return render_template("dashboard.html",
                           students=students,
                           departments=departments,
                           semesters=semesters,
                           sports=sports,
                           genders=genders,
                           students_count=students_count,
                           registrations_count=registrations_count,
                           gender_counts=list(gender_counts.values()))


@app.route("/admin/export_pdf")
@login_required
def export_pdf():
    department = request.args.get('department')
    semester = request.args.get('semester')
    sport = request.args.get('sport')
    gender = request.args.get('gender')  # Get gender from request

    db = get_db()
    db.row_factory = sqlite3.Row 
    cur = db.cursor()
    
    # 1. Base Query - Include st.gender in the selection
    query = """
        SELECT st.full_name, st.roll_number, st.email, st.student_id, st.department, st.semester, st.gender,
               GROUP_CONCAT(sp.name, ', ') as sports_list
        FROM students st
        LEFT JOIN registrations r ON st.id = r.student_id
        LEFT JOIN sports sp ON r.sport_id = sp.id
        WHERE 1=1
    """
    params = []

    # 2. Dynamic Filtering
    if department:
        query += " AND st.department = ?"
        params.append(department)
    if semester:
        query += " AND st.semester = ?"
        params.append(semester)
    if gender: # New Gender Filter Logic
        query += " AND st.gender = ?"
        params.append(gender)
    if sport:
        query += " AND st.id IN (SELECT student_id FROM registrations r2 JOIN sports sp2 ON r2.sport_id = sp2.id WHERE sp2.name = ?)"
        params.append(sport)

    query += " GROUP BY st.id"
    
    cur.execute(query, params)
    rows = cur.fetchall()

    # 3. Logic to switch Templates
    if sport and sport.strip() != "":
        template_name = "pdf_template_sport_specific.html"
    else:
        template_name = "pdf_template.html"

    # Pass selected_gender to the template
    html = render_template(
        template_name, 
        students=rows, 
        selected_sport=sport,
        selected_dept=department,
        selected_sem=semester,
        selected_gender=gender,
        now=datetime.now()
    )

    # 4. PDF Generation Options
    options = {
        'enable-local-file-access': None,
        'encoding': "UTF-8",
        'quiet': '',
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.8in',
        'margin-left': '0.5in',
    }
    
    try:
        pdf = pdfkit.from_string(html, False, options=options)
        return send_file(
            BytesIO(pdf),
            download_name=f"SportMeet_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
            as_attachment=True,
            mimetype='application/pdf'
        )
    except Exception as e:
        return f"Error generating PDF: {str(e)}", 500