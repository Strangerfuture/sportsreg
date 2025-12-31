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
