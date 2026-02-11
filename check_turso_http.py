"""Check Turso database using HTTP API."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

# Convert libsql:// to https://
url = DATABASE_URL.replace('libsql://', 'https://')

print(f"📊 Connecting to Turso: {url[:60]}...")
print(f"🔑 Token: {TURSO_AUTH_TOKEN[:20]}..." if TURSO_AUTH_TOKEN else "❌ NO TOKEN")

headers = {
    'Authorization': f'Bearer {TURSO_AUTH_TOKEN}',
    'Content-Type': 'application/json'
}

def execute_sql(sql):
    """Execute SQL via Turso HTTP API."""
    try:
        response = requests.post(
            url,
            headers=headers,
            json={'statements': [sql]}
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

# Check tables
print("\n📋 Checking tables...")
result = execute_sql("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")

if result and result[0].get('results'):
    rows = result[0]['results'].get('rows', [])
    if not rows:
        print("❌ NO TABLES FOUND! Database is empty.")
        print("\n🔧 SOLUTION: You need to initialize the database on Render.")
        print("   Option 1: Run migrations on Render")
        print("   Option 2: Use sync_to_turso.py to copy from local SQLite")
    else:
        print(f"✅ Found {len(rows)} tables:")
        for row in rows:
            table_name = row[0]
            count_result = execute_sql(f"SELECT COUNT(*) FROM {table_name}")
            if count_result and count_result[0].get('results'):
                count = count_result[0]['results']['rows'][0][0]
                print(f"   - {table_name}: {count} rows")

# Check admin user
print("\n👤 Checking for admin user...")
result = execute_sql("SELECT id, email, role, is_active FROM user WHERE email='admin@isufst.edu.ph'")

if result and result[0].get('results') and result[0]['results'].get('rows'):
    admin = result[0]['results']['rows'][0]
    print(f"✅ Admin user exists:")
    print(f"   ID: {admin[0]}")
    print(f"   Email: {admin[1]}")
    print(f"   Role: {admin[2]}")
    print(f"   Active: {admin[3]}")
else:
    print("❌ Admin user NOT FOUND!")
    print("\n🔧 SOLUTION: Create admin user with:")
    print("   python create_admin.py")

# Check all users
print("\n👥 Checking all users...")
result = execute_sql("SELECT email, role FROM user LIMIT 10")

if result and result[0].get('results') and result[0]['results'].get('rows'):
    users = result[0]['results']['rows']
    print(f"Found {len(users)} users:")
    for user in users:
        print(f"   - {user[0]} ({user[1]})")
else:
    print("❌ No users found in database")

print("\n✅ Check complete!")
