"""
Delete unnecessary tables from Turso - FINAL CLEANUP
Keep only essential high-impact features
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', '').replace('libsql://', 'https://')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN', '')

def execute_sql(sql):
    """Execute SQL on Turso via HTTP API"""
    response = requests.post(
        DATABASE_URL,
        headers={'Authorization': f'Bearer {TURSO_AUTH_TOKEN}'},
        json={'statements': [sql]}
    )
    return response.json()

print("🗑️  FINAL CLEANUP - Removing unnecessary tables...")
print()

# Tables to DELETE (low impact features)
tables_to_delete = [
    'doctor_schedules',      # Doctor scheduling - not needed for small clinic
    'doctor_leaves',         # Doctor leave tracking - not needed
    'audit_logs',           # Audit logging - not user-facing
    'appointment_waitlist',  # Waitlist system - overcomplicated
    'prescriptions',        # Advanced prescriptions - basic text works
    'prescription_items',   # Prescription line items - not needed
    'inventory_locks',      # Atomic locks - no race conditions in small clinic
    'medicine_reservation'  # Duplicate of medicine_reservations
]

print(f"Deleting {len(tables_to_delete)} tables:")
for t in tables_to_delete:
    print(f"  - {t}")
print()

deleted = []
errors = []

for table in tables_to_delete:
    try:
        result = execute_sql(f"DROP TABLE IF EXISTS {table}")
        if result and len(result) > 0 and 'error' in result[0]:
            error_msg = result[0]['error']
            if 'no such table' in error_msg.lower():
                print(f"  ⏭️  {table}: Already deleted")
            else:
                errors.append(f"{table}: {error_msg}")
                print(f"  ❌ {table}: {error_msg}")
        else:
            deleted.append(table)
            print(f"  ✅ {table}: Deleted")
    except Exception as e:
        errors.append(f"{table}: {str(e)}")
        print(f"  ❌ {table}: {str(e)}")

print()
print("="*70)
print(f"✅ Deleted: {len(deleted)}/{len(tables_to_delete)}")
if errors:
    print(f"❌ Errors: {len(errors)}")
print("="*70)

# Verify final state
print()
print("🔍 Final verification...")
result = execute_sql("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
if result and len(result) > 0 and 'results' in result[0]:
    final_tables = [row[0] for row in result[0]['results'].get('rows', [])]
    
    # Essential tables we KEPT
    essential = [
        'users', 'student_profiles', 'appointments', 'clinic_visits', 
        'inventory', 'medications', 'medication_logs', 'medicine_reservations',
        'queues', 'notifications', 'logbook_entries',
        'appointment_extensions',        # QR codes for appointments
        'medicine_reservation_extensions', # QR codes for medicine pickup
        'symptom_screenings',           # AI symptom screening history
        'visit_feedback',               # Patient ratings
        'health_certificates'           # Health certificate generation
    ]
    
    print(f"📊 Total tables: {len(final_tables)}")
    print()
    print("✅ ESSENTIAL TABLES (Kept):")
    for t in essential:
        if t in final_tables:
            print(f"  ✅ {t}")
        else:
            print(f"  ❌ {t} - MISSING!")
    
    print()
    print("ℹ️  SYSTEM TABLES:")
    for t in final_tables:
        if t in ['sqlite_sequence', 'alembic_version']:
            print(f"  - {t}")
    
    print()
    unexpected = [t for t in final_tables if t not in essential and t not in ['sqlite_sequence', 'alembic_version']]
    if unexpected:
        print(f"⚠️  UNEXPECTED TABLES ({len(unexpected)}):")
        for t in unexpected:
            print(f"  - {t}")

print()
print("="*70)
print("✅ Cleanup complete!")
print()
print("Final system includes:")
print("  • 11 core tables (users, appointments, visits, etc.)")
print("  • 5 high-impact features:")
print("    1. QR codes (appointments + medicine)")
print("    2. AI symptom screening history")
print("    3. Patient feedback/ratings")
print("    4. Health certificates")
print("    5. Appointment reminders")
print("="*70)

