"""Create admin user directly in Turso production database."""
import os
import requests
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

url = DATABASE_URL.replace('libsql://', 'https://')

print("🔐 Creating admin user in Turso production database...")
print(f"📊 Database: {url[:60]}...")

headers = {
    'Authorization': f'Bearer {TURSO_AUTH_TOKEN}',
    'Content-Type': 'application/json'
}

# Check if admin exists
print("\n1️⃣ Checking for existing admin...")
response = requests.post(
    url,
    headers=headers,
    json={'statements': ["SELECT id, email FROM users WHERE email='admin@isufst.edu.ph'"]}
)

if response.status_code == 200:
    result = response.json()
    if result[0].get('results', {}).get('rows'):
        print("✅ Admin user already exists!")
        admin = result[0]['results']['rows'][0]
        print(f"   ID: {admin[0]}")
        print(f"   Email: {admin[1]}")
        print("\n💡 You can now login with: admin@isufst.edu.ph / admin123")
    else:
        print("❌ Admin user not found. Creating...")
        
        # Generate password hash
        password_hash = generate_password_hash('admin123')
        now = datetime.now(timezone.utc).isoformat()
        
        # Create admin user
        insert_sql = f"""
        INSERT INTO users (email, password_hash, first_name, last_name, role, is_active, created_at, updated_at)
        VALUES ('admin@isufst.edu.ph', '{password_hash}', 'Admin', 'User', 'admin', 1, '{now}', '{now}')
        """
        
        response = requests.post(
            url,
            headers=headers,
            json={'statements': [insert_sql]}
        )
        
        if response.status_code == 200:
            print("✅ Admin user created successfully!")
            print("   Email: admin@isufst.edu.ph")
            print("   Password: admin123")
            print("\n🎉 You can now login on your Render production site!")
            print("   ⚠️  Change this password after first login")
        else:
            print(f"❌ Failed to create admin: {response.status_code}")
            print(response.text)
else:
    print(f"❌ Database query failed: {response.status_code}")
    print(response.text)

# Also check total user count
print("\n2️⃣ Checking total users in database...")
response = requests.post(
    url,
    headers=headers,
    json={'statements': ["SELECT COUNT(*) FROM users"]}
)

if response.status_code == 200:
    result = response.json()
    count = result[0]['results']['rows'][0][0]
    print(f"📊 Total users: {count}")
else:
    print("❌ Could not check user count")

print("\n✅ Done!")
