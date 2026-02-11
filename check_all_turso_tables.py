"""Quick check of Turso tables"""
import os, requests
from dotenv import load_dotenv
load_dotenv()

url = os.getenv('DATABASE_URL', '').replace('libsql://', 'https://')
token = os.getenv('TURSO_AUTH_TOKEN', '')

response = requests.post(
    url, 
    headers={'Authorization': f'Bearer {token}'}, 
    json={'statements': ["SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"]}
)

result = response.json()

if result and len(result) > 0 and 'results' in result[0]:
    tables = [row[0] for row in result[0]['results'].get('rows', [])]
    print(f'📊 TURSO DATABASE - Total tables: {len(tables)}\n')
    
    required = ['users', 'student_profiles', 'appointments', 'clinic_visits', 
                'inventory', 'medicine_reservations', 'queues', 'notifications', 'logbook_entries']
    
    print('='*70)
    print('REQUIRED TABLES (9 core for website to work):')
    print('='*70)
    missing = []
    for t in required:
        if t in tables:
            print(f'  ✅ {t}')
        else:
            print(f'  ❌ {t} - MISSING!')
            missing.append(t)
    
    print()
    print('='*70)
    print(f'EXTRA/OPTIONAL TABLES ({len([t for t in tables if t not in required and t != "sqlite_sequence"])} tables):')
    print('='*70)
    for t in tables:
        if t not in required and t != 'sqlite_sequence':
            print(f'  ℹ️  {t} (migration/extension - can be ignored)')
    
    print()
    print('='*70)
    if missing:
        print(f'⚠️  PROBLEM: {len(missing)} required tables are MISSING!')
        print(f'   Missing: {", ".join(missing)}')
        print('   Your website WILL NOT WORK without these tables!')
    else:
        print('✅ All 9 required tables exist!')
        print('   Your website can work properly.')
    print('='*70)
else:
    print('❌ Error:', result)
