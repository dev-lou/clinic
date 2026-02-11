import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    @staticmethod
    def _get_database_uri():
        """Get database URI - supports Turso (libsql) and local SQLite."""
        basedir = os.path.abspath(os.path.dirname(__file__))
        default_db = f'sqlite:///{os.path.join(basedir, "instance", "carehub_dev.db")}'
        uri = os.environ.get('DATABASE_URL', default_db)
        
        # Use Turso remote database via sqlalchemy-libsql driver
        if uri.startswith('libsql://'):
            auth_token = os.environ.get('TURSO_AUTH_TOKEN', '')
            # Check if sqlalchemy-libsql driver is available
            try:
                import sqlalchemy_libsql  # noqa: F401
                driver_available = True
            except ImportError:
                driver_available = False
            
            if driver_available and auth_token:
                host = uri.replace('libsql://', '')
                print(f"🚀 Using Turso Cloud Database: {host}")
                return f'sqlite+libsql://{host}?authToken={auth_token}&secure=true'
            else:
                # Fallback to local SQLite for development (driver not installed)
                print("⚠️  sqlalchemy-libsql not available — using local SQLite for development")
                os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
                return default_db
        
        # Ensure instance directory exists for local SQLite
        os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
        return uri
    
    SQLALCHEMY_DATABASE_URI = _get_database_uri.__func__()
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
