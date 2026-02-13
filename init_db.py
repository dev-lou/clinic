import os
from app import create_app
from models import db, User

def init_db():
    """Initialize the database and seed admin account."""
    app = create_app()
    with app.app_context():
        try:
            print("📋 Creating database tables (if they don't exist)...")
            db.create_all()
            print("✅ Database tables ready")
            
            # Auto-seed admin account
            admin = User.query.filter_by(email='admin@isufst.edu.ph').first()
            if not admin:
                print("creating admin account...")
                admin = User(
                    email='admin@isufst.edu.ph',
                    first_name='Admin',
                    last_name='CareHub',
                    role='admin'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print('🔑 Admin account created: admin@isufst.edu.ph / admin123')
            else:
                print('✅ Admin account already exists')
        except Exception as e:
            print(f"⚠️  Database initialization warning: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    init_db()
