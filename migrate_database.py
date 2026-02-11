"""
Database migration script to add all new tables.
Run this after installing dependencies: python migrate_database.py
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from models import db
from models_extended import (
    DoctorSchedule, DoctorLeave, AppointmentExtended, 
    AppointmentWaitlist, Prescription, PrescriptionItem,
    InventoryLock, VisitFeedback, AuditLog, 
    HealthCertificate, SymptomScreening
)

def run_migration():
    """Create all new tables."""
    app = create_app()
    
    with app.app_context():
        print("🔄 Starting database migration...")
        
        try:
            # Create all tables
            db.create_all()
            print("✅ All tables created successfully!")
            
            # List created tables
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n📋 Total tables: {len(tables)}")
            print("\n🆕 New extended tables:")
            new_tables = [
                'doctor_schedules', 'doctor_leaves', 'appointment_extensions',
                'appointment_waitlist', 'prescriptions', 'prescription_items',
                'inventory_locks', 'visit_feedback', 'audit_logs',
                'health_certificates', 'symptom_screenings'
            ]
            
            for table in new_tables:
                if table in tables:
                    print(f"  ✓ {table}")
                else:
                    print(f"  ✗ {table} (not found)")
            
            print("\n✨ Migration completed!")
            print("\n📝 Next steps:")
            print("  1. Run: pip install -r requirements.txt")
            print("  2. Run: npm install (for Tailwind CSS)")
            print("  3. Run: npm run build:css")
            print("  4. Start app: python app.py")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    run_migration()
