"""
Fix Turso database schema by adding missing columns
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TURSO_DATABASE_URL = os.getenv('DATABASE_URL', '').replace('libsql://', 'https://')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN', '')

def execute_sql(sql):
    """Execute SQL on Turso via HTTP API"""
    response = requests.post(
        TURSO_DATABASE_URL,
        headers={'Authorization': f'Bearer {TURSO_AUTH_TOKEN}'},
        json={'statements': [sql]}
    )
    return response.json()

print("🔧 Fixing Turso Schema...")
print()

# SQL statements to add missing columns
alterations = [
    # appointments table
    ("appointments", "ALTER TABLE appointments ADD COLUMN notes TEXT"),
    ("appointments", "ALTER TABLE appointments ADD COLUMN doctor_id INTEGER"),
    ("appointments", "ALTER TABLE appointments ADD COLUMN dentist_id INTEGER"),
    ("appointments", "ALTER TABLE appointments ADD COLUMN updated_at TIMESTAMP"),
    
    # clinic_visits table
    ("clinic_visits", "ALTER TABLE clinic_visits ADD COLUMN vital_signs TEXT"),
    ("clinic_visits", "ALTER TABLE clinic_visits ADD COLUMN prescription TEXT"),
    ("clinic_visits", "ALTER TABLE clinic_visits ADD COLUMN doctor_id INTEGER"),
    ("clinic_visits", "ALTER TABLE clinic_visits ADD COLUMN created_at TIMESTAMP"),
    
    # inventory table
    ("inventory", "ALTER TABLE inventory ADD COLUMN medicine_name VARCHAR(200)"),
    ("inventory", "ALTER TABLE inventory ADD COLUMN batch_number VARCHAR(100)"),
    ("inventory", "ALTER TABLE inventory ADD COLUMN date_received DATE"),
    ("inventory", "ALTER TABLE inventory ADD COLUMN created_at TIMESTAMP"),
    ("inventory", "ALTER TABLE inventory ADD COLUMN updated_at TIMESTAMP"),
    
    # medicine_reservations table
    ("medicine_reservations", "ALTER TABLE medicine_reservations ADD COLUMN created_at TIMESTAMP"),
    ("medicine_reservations", "ALTER TABLE medicine_reservations ADD COLUMN updated_at TIMESTAMP"),
    
    # queues table
    ("queues", "ALTER TABLE queues ADD COLUMN student_id INTEGER"),
    ("queues", "ALTER TABLE queues ADD COLUMN queue_number INTEGER"),
    ("queues", "ALTER TABLE queues ADD COLUMN priority INTEGER"),
    ("queues", "ALTER TABLE queues ADD COLUMN called_at TIMESTAMP"),
    ("queues", "ALTER TABLE queues ADD COLUMN service_type VARCHAR(50)"),
    ("queues", "ALTER TABLE queues ADD COLUMN created_at TIMESTAMP"),
    
    # logbook_entries table
    ("logbook_entries", "ALTER TABLE logbook_entries ADD COLUMN created_at TIMESTAMP"),
]

print(f"📋 Adding {len(alterations)} missing columns...\n")

success_count = 0
error_count = 0

for table, sql in alterations:
    try:
        result = execute_sql(sql)
        
        # Check if successful
        if result and isinstance(result, list) and len(result) > 0:
            if 'error' in result[0]:
                # Check if error is "duplicate column" which means it already exists
                error_msg = result[0]['error']
                if 'duplicate column' in error_msg.lower():
                    print(f"  ⏭️  {table}: Column already exists")
                    success_count += 1
                else:
                    print(f"  ❌ {table}: {error_msg}")
                    error_count += 1
            else:
                print(f"  ✅ {table}: Column added")
                success_count += 1
        else:
            print(f"  ✅ {table}: Column added")
            success_count += 1
            
    except Exception as e:
        print(f"  ❌ {table}: {str(e)}")
        error_count += 1

print()
print("="*60)
print(f"✅ Success: {success_count}/{len(alterations)}")
if error_count > 0:
    print(f"❌ Errors: {error_count}")
print("="*60)
print()
print("🔍 Run validate_turso_database.py to verify!")
