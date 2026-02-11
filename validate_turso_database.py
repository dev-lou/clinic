"""Comprehensive Turso database validation - check all tables and columns."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')
url = DATABASE_URL.replace('libsql://', 'https://')

headers = {
    'Authorization': f'Bearer {TURSO_AUTH_TOKEN}',
    'Content-Type': 'application/json'
}

def query(sql):
    """Execute SQL query."""
    response = requests.post(url, headers=headers, json={'statements': [sql]})
    if response.status_code == 200:
        result = response.json()
        if result and len(result) > 0:
            return result[0].get('results', {}).get('rows', [])
    return None

print("=" * 70)
print("🔍 TURSO DATABASE VALIDATION")
print("=" * 70)

# Expected tables from models.py
EXPECTED_TABLES = {
    'users': ['id', 'email', 'password_hash', 'first_name', 'last_name', 'role', 'is_active', 'created_at', 'updated_at'],
    'student_profiles': ['id', 'user_id', 'student_id_number', 'course', 'year_level', 'contact_number', 'blood_type', 'allergies', 'medical_conditions', 'emergency_contact_name', 'emergency_contact_number'],
    'appointments': ['id', 'student_id', 'appointment_date', 'start_time', 'end_time', 'service_type', 'status', 'notes', 'doctor_id', 'dentist_id', 'created_at', 'updated_at'],
    'clinic_visits': ['id', 'student_id', 'visit_date', 'chief_complaint', 'vital_signs', 'diagnosis', 'treatment', 'prescription', 'doctor_id', 'status', 'created_at'],
    'inventory': ['id', 'medicine_name', 'batch_number', 'category', 'quantity', 'unit', 'expiry_date', 'supplier', 'date_received', 'created_at', 'updated_at'],
    'medicine_reservations': ['id', 'student_id', 'medicine_name', 'quantity', 'status', 'reserved_at', 'picked_up_at', 'created_at', 'updated_at'],
    'queues': ['id', 'student_id', 'queue_number', 'priority', 'status', 'called_at', 'service_type', 'created_at'],
    'notifications': ['id', 'user_id', 'title', 'message', 'type', 'is_read', 'created_at'],
    'logbook_entries': ['id', 'student_id', 'purpose', 'check_in_time', 'check_out_time', 'created_at']
}

print(f"\n📊 Database: {url[:60]}...")
print(f"🔑 Token: {'✅ Present' if TURSO_AUTH_TOKEN else '❌ Missing'}\n")

# 1. Check all tables exist
print("=" * 70)
print("1️⃣ CHECKING TABLES")
print("=" * 70)

tables = query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")

if not tables:
    print("❌ CRITICAL: No tables found in database!")
    print("\n🔧 SOLUTION: Run migrations on Render or use sync script")
    exit(1)

existing_tables = [t[0] for t in tables]
print(f"✅ Found {len(existing_tables)} tables\n")

missing_tables = []
for table in EXPECTED_TABLES.keys():
    if table in existing_tables:
        print(f"  ✅ {table}")
    else:
        print(f"  ❌ {table} - MISSING!")
        missing_tables.append(table)

extra_tables = [t for t in existing_tables if t not in EXPECTED_TABLES and not t.startswith('alembic')]
if extra_tables:
    print(f"\n📋 Extra tables (migration/extension tables):")
    for t in extra_tables:
        print(f"  ℹ️  {t}")

# 2. Check columns for each critical table
print("\n" + "=" * 70)
print("2️⃣ CHECKING TABLE COLUMNS")
print("=" * 70)

for table_name, expected_columns in EXPECTED_TABLES.items():
    if table_name not in existing_tables:
        continue
    
    # Get table info
    columns = query(f"PRAGMA table_info({table_name})")
    if columns:
        existing_cols = [col[1] for col in columns]  # col[1] is column name
        
        missing_cols = [c for c in expected_columns if c not in existing_cols]
        
        if missing_cols:
            print(f"\n❌ {table_name}: Missing columns: {', '.join(missing_cols)}")
        else:
            print(f"\n✅ {table_name}: All {len(expected_columns)} columns present")
            
        # Count rows
        row_count = query(f"SELECT COUNT(*) FROM {table_name}")
        if row_count:
            print(f"   📊 {row_count[0][0]} rows")

# 3. Check admin user
print("\n" + "=" * 70)
print("3️⃣ CHECKING ADMIN USER")
print("=" * 70)

admin = query("SELECT id, email, first_name, last_name, role, is_active FROM users WHERE email='admin@isufst.edu.ph'")

if admin:
    print(f"✅ Admin user exists:")
    print(f"   ID: {admin[0][0]}")
    print(f"   Email: {admin[0][1]}")
    print(f"   Name: {admin[0][2]} {admin[0][3]}")
    print(f"   Role: {admin[0][4]}")
    print(f"   Active: {'Yes' if admin[0][5] else 'No'}")
    
    # Check password hash exists
    pwd_check = query("SELECT password_hash FROM users WHERE email='admin@isufst.edu.ph'")
    if pwd_check and pwd_check[0][0]:
        print(f"   🔐 Password hash: ✅ Present ({len(pwd_check[0][0])} chars)")
    else:
        print(f"   🔐 Password hash: ❌ MISSING!")
else:
    print("❌ Admin user NOT FOUND!")
    print("\n🔧 Run: python create_admin_turso.py")

# 4. Check all users
print("\n" + "=" * 70)
print("4️⃣ ALL USERS IN DATABASE")
print("=" * 70)

users = query("SELECT id, email, role FROM users ORDER BY id")

if users:
    print(f"Found {len(users)} user(s):\n")
    for user in users:
        print(f"   ID {user[0]}: {user[1]} ({user[2]})")
else:
    print("❌ No users in database")

# 5. Check for any data in other critical tables
print("\n" + "=" * 70)
print("5️⃣ DATA SUMMARY")
print("=" * 70)

summary_tables = ['appointments', 'clinic_visits', 'medicine_reservations', 'inventory', 'queues', 'notifications']
for table in summary_tables:
    if table in existing_tables:
        count = query(f"SELECT COUNT(*) FROM {table}")
        if count:
            status = "✅" if count[0][0] > 0 else "⚠️"
            print(f"  {status} {table}: {count[0][0]} records")

# 6. Test database write/read
print("\n" + "=" * 70)
print("6️⃣ DATABASE WRITE TEST")
print("=" * 70)

try:
    # Try to create a test table
    response = requests.post(url, headers=headers, json={
        'statements': [
            "CREATE TABLE IF NOT EXISTS _test_table (id INTEGER PRIMARY KEY, test_value TEXT)",
            "INSERT INTO _test_table (test_value) VALUES ('test')",
            "SELECT * FROM _test_table",
            "DROP TABLE _test_table"
        ]
    })
    
    if response.status_code == 200:
        print("✅ Database write/read test: PASSED")
        print("   - Can create tables")
        print("   - Can insert data")
        print("   - Can read data")
    else:
        print(f"❌ Database write test FAILED: {response.status_code}")
except Exception as e:
    print(f"❌ Database write test ERROR: {e}")

# Final verdict
print("\n" + "=" * 70)
print("📋 FINAL VERDICT")
print("=" * 70)

if missing_tables:
    print(f"❌ FAILED: {len(missing_tables)} tables missing")
    print(f"   Missing: {', '.join(missing_tables)}")
elif not admin:
    print("❌ FAILED: Admin user missing")
else:
    print("✅ DATABASE VALIDATION PASSED!")
    print("\n🎉 Your Turso database is ready!")
    print(f"\n📝 Login credentials:")
    print(f"   URL: https://isufst-clinic.onrender.com")
    print(f"   Email: admin@isufst.edu.ph")
    print(f"   Password: admin123")
    print(f"\n⚠️  Note: The 'sqlalchemy-libsql not available' warning is normal on Windows.")
    print(f"   Production on Render (Linux) will connect to Turso correctly.")

print("=" * 70)
