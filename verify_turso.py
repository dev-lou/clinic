"""Verify Turso database setup."""
import os
from dotenv import load_dotenv
import libsql_client

load_dotenv()


def verify_turso():
    """Verify Turso database tables and users."""
    print("=" * 60)
    print("  TURSO DATABASE VERIFICATION")
    print("=" * 60)
    
    try:
        # Connect to Turso
        database_url = os.environ.get('DATABASE_URL', '').replace('libsql://', 'https://')
        auth_token = os.environ.get('TURSO_AUTH_TOKEN', '')
        
        turso = libsql_client.create_client_sync(
            url=database_url,
            auth_token=auth_token
        )
        
        print("✅ Connected to Turso\n")
        
        # List all tables
        print("📋 Tables in database:")
        result = turso.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        if hasattr(result, 'rows') and result.rows:
            for row in result.rows:
                print(f"   - {row[0]}")
        print()
        
        # Check users table
        print("👤 Users in database:")
        result = turso.execute("SELECT id, email, first_name, last_name, role, is_active FROM users")
        if hasattr(result, 'rows') and result.rows:
            for row in result.rows:
                status = "Active" if row[5] else "Inactive"
                print(f"   ID: {row[0]} | {row[2]} {row[3]} ({row[1]}) | Role: {row[4]} | {status}")
        else:
            print("   No users found")
        print()
        
        # Check student profiles
        print("📝 Student profiles:")
        result = turso.execute("SELECT COUNT(*) FROM student_profiles")
        count = result.rows[0][0] if hasattr(result, 'rows') and result.rows else 0
        print(f"   Total: {count}")
        print()
        
        # Check appointments
        print("📅 Appointments:")
        result = turso.execute("SELECT COUNT(*) FROM appointments")
        count = result.rows[0][0] if hasattr(result, 'rows') and result.rows else 0
        print(f"   Total: {count}")
        print()
        
        # Check inventory
        print("💊 Inventory items:")
        result = turso.execute("SELECT COUNT(*) FROM inventory")
        count = result.rows[0][0] if hasattr(result, 'rows') and result.rows else 0
        print(f"   Total: {count}")
        
        print("\n✅ Verification complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)


if __name__ == '__main__':
    verify_turso()
