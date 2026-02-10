"""Initialize Turso database with tables from models."""
import os
import sys
import asyncio
from dotenv import load_dotenv
import libsql_client

# Load environment variables
load_dotenv()

# Don't import models yet to avoid naming conflicts with queue.py
# We'll define the table schemas directly


def get_create_table_sql():
    """Generate CREATE TABLE statements for all models."""
    
    # These are the SQL CREATE statements based on your models
    statements = [
        # User table
        """
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            student_id TEXT UNIQUE,
            contact_number TEXT,
            date_of_birth DATE,
            sex TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Queue table
        """
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Waiting',
            check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            served_time TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
        """,
        
        # Appointment table
        """
        CREATE TABLE IF NOT EXISTS appointment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            appointment_date DATE NOT NULL,
            appointment_time TEXT NOT NULL,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'Scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
        """,
        
        # ClinicVisit table
        """
        CREATE TABLE IF NOT EXISTS clinic_visit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            visit_date DATE NOT NULL,
            visit_time TEXT,
            chief_complaint TEXT,
            diagnosis TEXT,
            treatment TEXT,
            prescribed_medicines TEXT,
            vital_signs TEXT,
            notes TEXT,
            attended_by TEXT,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
        """,
        
        # Inventory table
        """
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            unit TEXT,
            expiry_date DATE,
            supplier TEXT,
            cost_per_unit REAL,
            reorder_level INTEGER DEFAULT 10,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
        """,
        
        # MedicineReservation table
        """
        CREATE TABLE IF NOT EXISTS medicine_reservation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            medicine_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            reservation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'Pending',
            claimed_date TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (medicine_id) REFERENCES inventory (id)
        )
        """
    ]
    
    return statements


async def initialize_turso_database():
    """Connect to Turso and create all tables."""
    
    # Get configuration from environment
    database_url = os.environ.get('DATABASE_URL', '')
    auth_token = os.environ.get('TURSO_AUTH_TOKEN', '')
    
    if not database_url or not database_url.startswith('libsql://'):
        print("❌ Error: DATABASE_URL must be a Turso URL (libsql://...)")
        print("   Check your .env file")
        return False
    
    if not auth_token:
        print("❌ Error: TURSO_AUTH_TOKEN is required")
        print("   Get your token by running: turso db tokens create <database-name>")
        return False
    
    try:
        # Convert libsql:// to https://
        url = database_url.replace('libsql://', 'https://')
        
        print(f"🔌 Connecting to Turso database: {database_url}")
        
        # Create Turso client (async)
        client = libsql_client.create_client_sync(
            url=url,
            auth_token=auth_token
        )
        
        print("✅ Connected successfully!")
        print("\n📋 Creating tables...")
        
        # Get all CREATE TABLE statements
        statements = get_create_table_sql()
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            table_name = statement.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
            print(f"   {i}. Creating table: {table_name}")
            result = client.execute(statement)
            print(f"      ✓ {table_name} created")
        
        print("\n✨ Database initialized successfully!")
        print(f"   Total tables created: {len(statements)}")
        
        # List tables to verify
        print("\n📊 Verifying tables...")
        result = client.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = result.rows
        
        if tables:
            print("   Tables in database:")
            for table in tables:
                print(f"   - {table[0]}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify your TURSO_AUTH_TOKEN is correct")
        print("2. Run: turso db tokens create clinic-dev-lou")
        print("3. Make sure your database exists: turso db list")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("  🏥 ISUFST CareHub - Turso Database Initialization")
    print("=" * 60)
    print()
    
    success = asyncio.run(initialize_turso_database())
    
    if not success:
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("  ✅ Setup Complete!")
    print("=" * 60)
    print("\nYou can now run your application:")
    print("  python app.py")
