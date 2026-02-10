import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///carehub_dev.db')

    @staticmethod
    def _fix_uri(uri):
        """Convert Turso URLs to SQLite format for local development.
        
        Note: For production Turso deployment, you'll need to use
        libsql_client directly (see turso_db.py helper).
        For local development, we use standard SQLite.
        """
        if not uri or uri.startswith('sqlite://'):
            # Already SQLite or empty, use as-is
            return uri or 'sqlite:///carehub_dev.db'
        elif uri.startswith('libsql://') or (uri.startswith('https://') and 'turso' in uri):
            # Turso URL: For local development, fall back to SQLite
            # For production, set up proper Turso connection
            print(f"Warning: Turso URL detected but using local SQLite. "
                  f"For production Turso, use turso_db.py helper.")
            return 'sqlite:///carehub_dev.db'
        return uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # Use local SQLite for development, or Turso URL if provided
    SQLALCHEMY_DATABASE_URI = Config._fix_uri(os.environ.get('DATABASE_URL') or 'sqlite:///carehub_dev.db')


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    @classmethod
    def init_app(cls):
        uri = os.environ.get('DATABASE_URL', '')
        if uri:
            cls.SQLALCHEMY_DATABASE_URI = Config._fix_uri(uri)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
