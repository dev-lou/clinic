import os
from dotenv import load_dotenv

load_dotenv()


def get_database_uri():
    """Get database URI - supports PostgreSQL, local SQLite, or Turso."""
    basedir = os.path.abspath(os.path.dirname(__file__))
    default_db = f'sqlite:///{os.path.join(basedir, "instance", "carehub_dev.db")}'
    uri = os.environ.get('DATABASE_URL', default_db)
    
    # For Turso - currently not supported without Rust compilation
    # Use PostgreSQL or SQLite instead
    if uri.startswith('libsql://'):
        print("⚠️  Turso (libsql://) URLs require Rust compilation which may fail on Render")
        print("📝 Using local SQLite instead. For production, consider PostgreSQL.")
        print("ℹ️  To use Turso: Install Rust locally or use PostgreSQL on Render")
        
        # Fall back to local SQLite
        os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
        return default_db
    
    # PostgreSQL support (recommended for Render production)
    if uri.startswith('postgresql://') or uri.startswith('postgres://'):
        # Fix postgres:// to postgresql:// for SQLAlchemy 1.4+
        if uri.startswith('postgres://'):
            uri = uri.replace('postgres://', 'postgresql://', 1)
        print("INFO: Using PostgreSQL database")
        return uri
    
    # Ensure instance directory exists for local SQLite
    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
    print("INFO: Using local SQLite database")
    return uri


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # Development uses the same database URI logic from base Config


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Production uses the same database URI logic from base Config


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
