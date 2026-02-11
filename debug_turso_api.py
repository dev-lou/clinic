"""Debug Turso API response format."""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')
url = DATABASE_URL.replace('libsql://', 'https://')

headers = {
    'Authorization': f'Bearer {TURSO_AUTH_TOKEN}',
    'Content-Type': 'application/json'
}

print("🔍 Testing Turso API...\n")

# Try simple query
response = requests.post(
    url,
    headers=headers,
    json={'statements': ["SELECT COUNT(*) as count FROM users"]}
)

print(f"Status: {response.status_code}")
print(f"\nFull Response:")
print(json.dumps(response.json(), indent=2))
