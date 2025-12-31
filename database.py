import os
from dotenv import load_dotenv # You may need to: pip install python-dotenv
from libsql_client import create_client_sync

# This loads the variables from your .env file into os.environ
load_dotenv() 

url = os.getenv("TURSO_DATABASE_URL")
auth_token = os.getenv("TURSO_AUTH_TOKEN")

# Robustness check: Ensure URL is not None before calling the client
if url is None:
    raise ValueError("TURSO_DATABASE_URL is not set in environment variables")


# Initialize the sync client
db = create_client_sync(url, auth_token=auth_token)

sports_list = [
    "Football", "Cricket", "Badminton", 
    "Chess", "Carrom Board", "Table Tennis"
]

for sport in sports_list:
    try:
        # 1. Use .execute()
        # 2. Pass sport inside a list [sport]
        db.execute(
            "INSERT INTO sports (name) VALUES (?)",
            [sport]
        )
        print(f"Inserted: {sport}")
    except Exception as e:
        print(f"Skipped: {sport} (Reason: {e})")