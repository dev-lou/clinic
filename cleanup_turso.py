"""Remove duplicate tables from Turso database."""
import os
import warnings
warnings.filterwarnings('ignore')
from dotenv import load_dotenv
import libsql_client

load_dotenv()


def get_turso_client():
    """Create Turso database client."""
    database_url = os.environ.get('DATABASE_URL', '').replace('libsql://', 'https://')
    auth_token = os.environ.get('TURSO_AUTH_TOKEN', '')
    
    return libsql_client.create_client_sync(
        url=database_url,
        auth_token=auth_token
    )


def remove_duplicate_tables():
    """Remove duplicate singular tables that are not used."""
    print("CLEANING TURSO DATABASE")
    print("-" * 40)
    
    # Duplicate singular tables to REMOVE
    duplicate_tables = ['user', 'appointment', 'clinic_visit', 'medicine_reservation', 'queue']
    
    try:
        turso = get_turso_client()
        
        print("Removing duplicate tables...")
        for table in duplicate_tables:
            turso.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  ✓ {table}")
        
        # Show final table list
        result = turso.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        final_tables = [row[0] for row in result.rows] if hasattr(result, 'rows') else []
        
        print("\nFinal tables:")
        for table in final_tables:
            print(f"  - {table}")
        
        print("\n✅ Cleanup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    remove_duplicate_tables()
