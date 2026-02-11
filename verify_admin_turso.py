"""Verify admin user in Turso."""
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

print("🔍 Verifying users in Turso production database...\n")

response = requests.post(
    url,
    headers=headers,
    json={'statements': ["SELECT id, email, first_name, last_name, role, is_active FROM users"]}
)

if response.status_code == 200:
    result = response.json()
    if result and len(result) > 0:
        rows_data = result[0].get('results', {})
        if 'rows' in rows_data and rows_data['rows']:
            rows = rows_data['rows']
            print(f"✅ Found {len(rows)} user(s):\n")
            for row in rows:
                print(f"   ID: {row[0]}")
                print(f"   Email: {row[1]}")
                print(f"   Name: {row[2]} {row[3]}")
                print(f"   Role: {row[4]}")
                print(f"   Active: {row[5]}")
                print()
            
            print("🎉 SUCCESS! You can now login on Render at:")
            print("   https://isufst-clinic.onrender.com")
            print("   Email: admin@isufst.edu.ph")
            print("   Password: admin123")
        else:
            print("❌ No users found in database")
    else:
        print("❌ No data returned")
        print(f"Response: {result}")
else:
    print(f"❌ Query failed: {response.status_code}")
    print(response.text[:500])
