"""Turso Database Wrapper for direct database access."""
import os
from functools import wraps
import libsql_client
from dotenv import load_dotenv

load_dotenv()

# Global Turso client connection
_turso_client = None


def get_turso_client():
    """Get or create Turso client connection."""
    global _turso_client
    
    if _turso_client is None:
        database_url = os.environ.get('DATABASE_URL', '')
        auth_token = os.environ.get('TURSO_AUTH_TOKEN', '')
        
        if database_url.startswith('libsql://'):
            # Convert libsql:// to https://
            url = database_url.replace('libsql://', 'https://')
            _turso_client = libsql_client.create_client_sync(
                url=url,
                auth_token=auth_token
            )
            print(f"✅ Connected to Turso: {database_url.split('//')[1]}")
        else:
            raise ValueError("DATABASE_URL must be a Turso libsql:// URL")
    
    return _turso_client


def use_turso_db(func):
    """Decorator to inject Turso client into route functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        turso = get_turso_client()
        return func(*args, turso=turso, **kwargs)
    return wrapper


# Initialize on import if Turso URL is present
if os.environ.get('DATABASE_URL', '').startswith('libsql://'):
    try:
        get_turso_client()
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize Turso client: {e}")
