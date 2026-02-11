import os
from dotenv import load_dotenv
import libsql_client

load_dotenv()

url = os.environ['DATABASE_URL'].replace('libsql://', 'https://')
token = os.environ['TURSO_AUTH_TOKEN']
turso = libsql_client.create_client_sync(url=url, auth_token=token)

print("Dropping duplicate tables...")
turso.execute("DROP TABLE IF EXISTS user")
turso.execute("DROP TABLE IF EXISTS appointment")
turso.execute("DROP TABLE IF EXISTS clinic_visit")
turso.execute("DROP TABLE IF EXISTS medicine_reservation")
turso.execute("DROP TABLE IF EXISTS queue")
print("Done!")

result = turso.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print("\nTables in database:")
for row in result.rows:
    print(f"  {row[0]}")
