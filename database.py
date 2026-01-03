import sqlite3

def get_db():
    conn = sqlite3.connect("sport.db")
    conn.row_factory = sqlite3.Row
    return conn

sports_list = [
    "Football", "Cricket", "Badminton",
    "Chess", "Musical Chair", "Table Tennis"
]

db = get_db()
cursor = db.cursor()

for sport in sports_list:
    try:
        cursor.execute(
            "INSERT INTO sports (name) VALUES (?)",
            (sport,)   # tuple is standard
        )
        print(f"Inserted: {sport}")
    except sqlite3.IntegrityError as e:
        print(f"Skipped: {sport} (Reason: {e})")

db.commit()
db.close()   
