import os
from dotenv import load_dotenv
import libsql_client

load_dotenv()

DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

# Use the synchronous client
client = libsql_client.create_client_sync(
    url=DATABASE_URL,
    auth_token=AUTH_TOKEN
)

def get_db():
    return client








# def export_pdf():
#     department = request.args.get('department')
#     semester = request.args.get('semester')
#     sport = request.args.get('sport')

#     db = get_db()
#     cur = db.cursor()
    
#     # ... (Your SQL query logic remains the same) ...
#     # Modified query using GROUP_CONCAT and GROUP BY
#     query = """
#         SELECT st.full_name, st.roll_number, st.email, st.department, st.semester, 
#                GROUP_CONCAT(sp.name, ', ') as sports_list
#         FROM students st
#         LEFT JOIN registrations r ON st.id = r.student_id
#         LEFT JOIN sports sp ON r.sport_id = sp.id
#         WHERE 1=1
#     """
#     params = []

#     if department:
#         query += " AND st.department = ?"
#         params.append(department)
#     if semester:
#         query += " AND st.semester = ?"
#         params.append(semester)
#     if sport:
#         # We use a subquery for the sport filter to ensure we still see 
#         # ALL sports for a student if they match the filtered one
#         query += " AND st.id IN (SELECT student_id FROM registrations r2 JOIN sports sp2 ON r2.sport_id = sp2.id WHERE sp2.name = ?)"
#         params.append(sport)

#     query += " GROUP BY st.id" # Crucial: collapse rows by student ID

#     cur.execute(query, params)
#     rows = cur.fetchall()
#         # 1. Get the absolute path to your project root
#         # This helps wkhtmltopdf find your CSS/Images on the disk
#     project_root = os.path.abspath(os.path.dirname(__file__))

#     # 2. Render HTML with the root path passed as a variable
#     html = render_template(
#         "pdf_template.html", 
#         students=rows, 
#         now=datetime.now(),
#         root_path=project_root
#     )

#     # 3. Add configuration options
#     options = {
#     'enable-local-file-access': None,
#     'encoding': "UTF-8",
#     'quiet': ''
# }
#     pdf_content = pdfkit.from_string(html, False, options=options)
#     # 5. Use BytesIO to send the PDF as a file object
#     return send_file(
#         BytesIO(pdf_content),
#         download_name="students_report.pdf",
#         as_attachment=True,
#         mimetype='application/pdf'
#     )