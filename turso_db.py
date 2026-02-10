"""Turso database connection helper for libSQL."""
import os
from urllib.parse import urlparse
import libsql_client


def get_turso_connection():
    """
    Create a Turso database connection.
    
    For Turso, you need:
    - TURSO_DATABASE_URL: Your Turso database URL (e.g., libsql://your-db.turso.io)
    - TURSO_AUTH_TOKEN: Your Turso authentication token
    
    For local development, just use DATABASE_URL=sqlite:///carehub_dev.db
    """
    database_url = os.environ.get('DATABASE_URL', '')
    
    # Check if it's a Turso URL
    if database_url.startswith('libsql://') or (database_url.startswith('https://') and 'turso' in database_url):
        auth_token = os.environ.get('TURSO_AUTH_TOKEN', '')
        
        if not auth_token:
            raise ValueError("TURSO_AUTH_TOKEN environment variable is required for Turso database")
        
        # Create Turso connection using libsql_client
        url = database_url.replace('libsql://', 'https://')
        conn = libsql_client.create_client(
            url=url,
            auth_token=auth_token
        )
        return conn
    
    # For local SQLite, return None (SQLAlchemy will handle it)
    return None


def is_turso_url(url):
    """Check if the provided URL is a Turso database URL."""
    if not url:
        return False
    return url.startswith('libsql://') or (url.startswith('https://') and 'turso' in url)
