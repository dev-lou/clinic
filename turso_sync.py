"""
Turso Cloud Database Sync Utility - Pure Python (No Rust required!)

This module provides sync between local SQLite and Turso cloud database
using the HTTP-based libsql-client (pure Python).
"""
import os
from libsql_client import create_client_sync


def get_turso_client():
    """Get Turso client using HTTP API (no Rust compilation needed)."""
    turso_url = os.environ.get('TURSO_DATABASE_URL')
    auth_token = os.environ.get('TURSO_AUTH_TOKEN')
    
    if not turso_url or not auth_token:
        return None
    
    try:
        client = create_client_sync(
            url=turso_url,
            auth_token=auth_token
        )
        return client
    except Exception as e:
        print(f"⚠️  Turso client creation failed: {e}")
        return None


def test_turso_connection():
    """Test Turso connection."""
    client = get_turso_client()
    if not client:
        print("❌ Turso client not available")
        return False
    
    try:
        result = client.execute("SELECT 1 as test")
        print(f"✅ Turso connection successful: {result}")
        return True
    except Exception as e:
        print(f"❌ Turso connection failed: {e}")
        return False


def sync_table_to_turso(local_conn, table_name):
    """Sync a table from local SQLite to Turso."""
    client = get_turso_client()
    if not client:
        return False
    
    try:
        # Get table data from local
        cursor = local_conn.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Sync to Turso
        # Note: This is a simple example. You'll need to handle schema creation and data types.
        print(f"ℹ️  Would sync {len(rows)} rows from {table_name} to Turso")
        
        return True
    except Exception as e:
        print(f"⚠️  Sync failed for {table_name}: {e}")
        return False


if __name__ == '__main__':
    test_turso_connection()
