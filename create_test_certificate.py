"""
Create test student with health certificate for demo purposes.
"""
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

load_dotenv()

# Use Turso if available
try:
    from turso_wrapper import get_turso_connection
    USE_TURSO = True
    print("✓ Using Turso Cloud Database")
except:
    USE_TURSO = False
    print("✓ Using Local SQLite Database")
    from app import create_app
    app = create_app()

if USE_TURSO:
    conn = get_turso_connection()
    
    # 1. Create test student user
    print("\n1️⃣ Creating test student...")
    from werkzeug.security import generate_password_hash
    password_hash = generate_password_hash('student123')
    
    conn.execute("""
        INSERT INTO users (email, password_hash, first_name, last_name, role, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ['test.student@isufst.edu.ph', password_hash, 'Maria', 'Santos', 'student', 1, datetime.now()])
    conn.commit()
    
    # Get student ID
    result = conn.execute("SELECT id FROM users WHERE email = ?", ['test.student@isufst.edu.ph'])
    student_id = result.fetchone()[0]
    print(f"   ✓ Created user ID: {student_id}")
    
    # 2. Create student profile
    print("\n2️⃣ Creating student profile...")
    conn.execute("""
        INSERT INTO student_profiles (user_id, student_id_number, course, year_level, blood_type, contact_number, emergency_contact_name, emergency_contact_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [student_id, '2024-12345', 'BS Computer Science', 3, 'O+', '09123456789', 'Rosa Santos', '09987654321'])
    conn.commit()
    print(f"   ✓ Created profile for Maria Santos (2024-12345)")
    
    # 3. Create completed clinic visit
    print("\n3️⃣ Creating completed clinic visit...")
    visit_date = date.today() - timedelta(days=2)
    conn.execute("""
        INSERT INTO clinic_visits (student_id, visit_date, chief_complaint, diagnosis, treatment, status, vital_signs)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        student_id,
        visit_date,
        'Medical clearance for sports',
        'General health check - All systems normal',
        'Patient cleared for physical activities',
        'completed',
        '{"bp": "120/80", "temp": "36.5", "hr": "72"}'
    ])
    conn.commit()
    print(f"   ✓ Created completed visit dated {visit_date}")
    
    # 4. Create health certificate
    print("\n4️⃣ Creating health certificate...")
    # Get admin ID for issued_by
    result = conn.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
    admin_id = result.fetchone()[0]
    
    cert_number = f"HC-{date.today().year}-0001"
    issued_at = datetime.now()
    valid_until = date.today() + timedelta(days=180)  # 6 months
    
    conn.execute("""
        INSERT INTO health_certificates (student_id, issued_by, certificate_number, purpose, medical_findings, issued_at, valid_until)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        student_id,
        admin_id,
        cert_number,
        'Sports Participation',
        f'Based on visit {visit_date.strftime("%b %d, %Y")}:\n\nDiagnosis: General health check - All systems normal\n\nTreatment: Patient cleared for physical activities\n\nStudent is fit for normal activities and sports participation.',
        issued_at,
        valid_until
    ])
    conn.commit()
    print(f"   ✓ Created certificate {cert_number}")
    
    conn.close()
    
else:
    # Local SQLite
    with app.app_context():
        from models import db, User, ClinicVisit, StudentProfile
        from models_extended import HealthCertificate
        
        # 1. Create test student
        print("\n1️⃣ Creating test student...")
        student = User(
            email='test.student@isufst.edu.ph',
            first_name='Maria',
            last_name='Santos',
            role='student',
            is_active=True
        )
        student.set_password('student123')
        db.session.add(student)
        db.session.commit()
        print(f"   ✓ Created user ID: {student.id}")
        
        # 2. Create student profile
        print("\n2️⃣ Creating student profile...")
        profile = StudentProfile(
            user_id=student.id,
            student_id_number='2024-12345',
            course='BS Computer Science',
            year_level=3,
            blood_type='O+',
            contact_number='09123456789',
            emergency_contact_name='Rosa Santos',
            emergency_contact_number='09987654321'
        )
        db.session.add(profile)
        db.session.commit()
        print(f"   ✓ Created profile for Maria Santos (2024-12345)")
        
        # 3. Create completed clinic visit
        print("\n3️⃣ Creating completed clinic visit...")
        visit_date = date.today() - timedelta(days=2)
        visit = ClinicVisit(
            student_id=student.id,
            visit_date=visit_date,
            chief_complaint='Medical clearance for sports',
            diagnosis='General health check - All systems normal',
            treatment='Patient cleared for physical activities',
            status='completed',
            vital_signs='{"bp": "120/80", "temp": "36.5", "hr": "72"}'
        )
        db.session.add(visit)
        db.session.commit()
        print(f"   ✓ Created completed visit dated {visit_date}")
        
        # 4. Create health certificate
        print("\n4️⃣ Creating health certificate...")
        admin = User.query.filter_by(role='admin').first()
        
        cert_number = f"HC-{date.today().year}-0001"
        valid_until = date.today() + timedelta(days=180)
        
        certificate = HealthCertificate(
            student_id=student.id,
            issued_by=admin.id,
            certificate_number=cert_number,
            purpose='Sports Participation',
            medical_findings=f'Based on visit {visit_date.strftime("%b %d, %Y")}:\n\nDiagnosis: General health check - All systems normal\n\nTreatment: Patient cleared for physical activities\n\nStudent is fit for normal activities and sports participation.',
            valid_until=valid_until
        )
        db.session.add(certificate)
        db.session.commit()
        print(f"   ✓ Created certificate {cert_number}")

print("\n" + "="*60)
print("✅ TEST DATA CREATED SUCCESSFULLY!")
print("="*60)
print("\n📋 Test Student Login Credentials:")
print("   Email:    test.student@isufst.edu.ph")
print("   Password: student123")
print("\n📝 Student Details:")
print("   Name:        Maria Santos")
print("   Student ID:  2024-12345")
print("   Course:      BS Computer Science - 3rd Year")
print("\n🏥 Health Certificate:")
print(f"   Number:      {cert_number}")
print("   Purpose:     Sports Participation")
print(f"   Valid Until: {valid_until.strftime('%B %d, %Y')}")
print("\n🎯 Next Steps:")
print("   1. Login as: test.student@isufst.edu.ph")
print("   2. Go to Dashboard")
print("   3. Scroll to 'Health Certificates' section (right column)")
print("   4. Click 'PDF' to download")
print("="*60)
