"""Check Turso database tables and admin user."""
import os
from dotenv import load_dotenv
import libsql_experimental as libsql

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

print(f"📊 Connecting to Turso: {DATABASE_URL[:50]}...")

try:
    # Connect to Turso
    url = DATABASE_URL.replace('libsql://', 'https://')
    conn = libsql.connect(database=url, auth_token=TURSO_AUTH_TOKEN)
    cursor = conn.cursor()
    
    # Check tables
    print("\n📋 Checking tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    if not tables:
        print("❌ NO TABLES FOUND! Database is empty.")
        print("\n🔧 You need to run migrations or initialize the database.")
        print("   Try running: flask db upgrade")
    else:
        print(f"✅ Found {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   - {table[0]}: {count} rows")
    
    # Check for admin user
    print("\n👤 Checking for admin user...")
    try:
        cursor.execute("SELECT id, email, role, is_active FROM user WHERE email='admin@isufst.edu.ph'")
        admin = cursor.fetchone()
        if admin:
            print(f"✅ Admin user exists:")
            print(f"   ID: {admin[0]}")
            print(f"   Email: {admin[1]}")
            print(f"   Role: {admin[2]}")
            print(f"   Active: {admin[3]}")
        else:
            print("❌ Admin user NOT FOUND!")
            print("   Expected: admin@isufst.edu.ph")
            print("\n🔧 You need to create the admin user.")
    except Exception as e:
        print(f"❌ Could not check for admin user: {e}")
        print("   (Table 'user' might not exist)")
    
    # Check all users
    try:
        cursor.execute("SELECT email, role FROM user LIMIT 10")
        users = cursor.fetchall()
        if users:
            print(f"\n👥 Sample users in database ({len(users)}):")
            for user in users:
                print(f"   - {user[0]} ({user[1]})")
    except:
        pass
    
    conn.close()
    print("\n✅ Database check complete!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTroubleshooting:")
    print("1. Check DATABASE_URL is correct")
    print("2. Check TURSO_AUTH_TOKEN is valid")
    print("3. Verify Turso database is accessible")
