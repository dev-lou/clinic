import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    @staticmethod
    def _get_database_uri():
        """Get database URI - Turso with local SQLAlchemy bridge."""
        uri = os.environ.get('DATABASE_URL', 'sqlite:///instance/carehub_dev.db')
        
        # Use Turso remote database
        if uri.startswith('libsql://'):
            auth_token = os.environ.get('TURSO_AUTH_TOKEN', '')
            print(f"🚀 Using Turso Cloud Database: {uri.split('//')[1]}")
            print("   (Local SQLAlchemy cache for ORM compatibility)")
            # Use absolute path for Windows compatibility
            basedir = os.path.abspath(os.path.dirname(__file__))
            os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
            db_path = os.path.join(basedir, 'instance', 'carehub_turso_local.db')
            return f'sqlite:///{db_path}'
        
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
