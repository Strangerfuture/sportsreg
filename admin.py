import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

def get_db():
    conn = sqlite3.connect("sport.db")
    conn.row_factory = sqlite3.Row
    return conn


def register():
    
    username = input("username :")
    password = input("password :")
        

    hash_pw = generate_password_hash(password)
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", (username, hash_pw))
        db.commit()
    except sqlite3.IntegrityError:
        print("Username already taken")
        return 1
    finally:
        db.close()

register()