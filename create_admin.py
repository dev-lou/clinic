"""Create admin user in local database."""
from app import create_app
from models import db, User
from datetime import datetime, timezone

app = create_app()

with app.app_context():
    # Check if admin already exists
    admin = User.query.filter_by(email='admin@isufst.edu.ph').first()
    
    if admin:
        print("✅ Admin user already exists")
        print(f"   Email: {admin.email}")
        print(f"   Name: {admin.first_name} {admin.last_name}")
        print(f"   Role: {admin.role}")
    else:
        # Create admin user
        admin = User(
            email='admin@isufst.edu.ph',
            first_name='Admin',
            last_name='User',
            role='admin',
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin user created successfully!")
        print("   Email: admin@isufst.edu.ph")
        print("   Password: admin123")
        print("   ⚠️  Change this password after first login!")
