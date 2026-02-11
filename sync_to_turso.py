"""Sync local SQLite database schema to Turso."""
import os
import sqlite3
from dotenv import load_dotenv
import libsql_client

load_dotenv()


def get_turso_client():
    """Create Turso database client."""
    database_url = os.environ.get('DATABASE_URL', '')
    auth_token = os.environ.get('TURSO_AUTH_TOKEN', '')
    
    if not database_url.startswith('libsql://'):
        raise ValueError("DATABASE_URL must be a Turso libsql:// URL")
    
    if not auth_token:
        raise ValueError("TURSO_AUTH_TOKEN is required")
    
    # Convert libsql:// to https://
    url = database_url.replace('libsql://', 'https://')
    
    return libsql_client.create_client_sync(
        url=url,
        auth_token=auth_token
    )


def get_local_schema():
    """Get CREATE TABLE statements from local SQLite database."""
    db_path = 'instance/carehub_turso_local.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("   Run: python -c \"from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()\"")
        return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    schemas = []
    for (table_name,) in tables:
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        create_sql = cursor.fetchone()[0]
        schemas.append(create_sql)
    
    conn.close()
    return schemas


def sync_schema_to_turso():
    """Sync schema from local SQLite to Turso."""
    print("🔄 Syncing schema to Turso...")
    
    try:
        # Get Turso client
        turso = get_turso_client()
        print("✅ Connected to Turso")
        
        # Get local schema
        schemas = get_local_schema()
        print(f"📋 Found {len(schemas)} tables to sync")
        
        # Execute each CREATE TABLE statement
        for schema in schemas:
            # Replace CREATE TABLE with CREATE TABLE IF NOT EXISTS
            schema = schema.replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS', 1)
            
            table_name = schema.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
            print(f"  Creating table: {table_name}")
            
            try:
                turso.execute(schema)
            except Exception as e:
                print(f"  ⚠️  Warning for {table_name}: {e}")
        
        print("\n✅ Schema synced successfully!")
        return turso
        
    except Exception as e:
        print(f"\n❌ Error syncing to Turso: {e}")
        return None


def create_admin_user(turso):
    """Create admin user in Turso if doesn't exist."""
    print("\n👤 Checking for admin user...")
    
    try:
        # Check if admin exists
        result = turso.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
        admin_count = result.rows[0][0] if hasattr(result, 'rows') and result.rows else 0
        
        if admin_count > 0:
            print(f"✅ Admin user already exists ({admin_count} admin(s))")
            return True
        
        # Create admin user
        print("Creating default admin user...")
        from werkzeug.security import generate_password_hash
        from datetime import datetime, timezone
        
        password_hash = generate_password_hash('admin123')
        created_at = datetime.now(timezone.utc).isoformat()
        
        turso.execute("""
            INSERT INTO users (email, password_hash, first_name, last_name, role, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ['admin@isufst.edu.ph', password_hash, 'Admin', 'User', 'admin', 1, created_at, created_at])
        
        print("✅ Admin user created!")
        print("   Email: admin@isufst.edu.ph")
        print("   Password: admin123")
        print("   ⚠️  Change this password after first login!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("  TURSO DATABASE SYNC")
    print("=" * 60)
    
    # Sync schema
    turso = sync_schema_to_turso()
    
    # Create admin user
    if turso:
        create_admin_user(turso)
    
    print("\n" + "=" * 60)
