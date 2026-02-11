"""Test admin login credentials."""
from app import create_app
from models import User

app = create_app()

with app.app_context():
    admin = User.query.filter_by(email='admin@isufst.edu.ph').first()
    
    if admin:
        print(f"User found: {admin.email}")
        print(f"Name: {admin.first_name} {admin.last_name}")
        print(f"Role: {admin.role}")
        print(f"Active: {admin.is_active}")
        
        # Test password
        test_password = 'admin123'
        if admin.check_password(test_password):
            print(f"\n✅ Password '{test_password}' is CORRECT")
        else:
            print(f"\n❌ Password '{test_password}' is INCORRECT")
            print("\nResetting password to 'admin123'...")
            admin.set_password('admin123')
            from models import db
            db.session.commit()
            print("✅ Password reset successfully!")
    else:
        print("❌ Admin user not found!")
