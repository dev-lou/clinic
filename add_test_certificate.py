"""
Quick script to add a test health certificate to an existing student.
"""
from app import create_app
from models import db, User, ClinicVisit
from models_extended import HealthCertificate
from datetime import datetime, date, timedelta

app = create_app()

with app.app_context():
    # Find a student
    student = User.query.filter_by(role='student').first()
    
    if not student:
        print("❌ No student found! Register a student first.")
        exit()
    
    print(f"✓ Found student: {student.full_name} ({student.email})")
    
    # Create a completed clinic visit if none exists
    existing_visit = ClinicVisit.query.filter_by(
        student_id=student.id,
        status='completed'
    ).first()
    
    if not existing_visit:
        print("\n📋 Creating a completed clinic visit...")
        visit_date = date.today() - timedelta(days=2)
        visit = ClinicVisit(
            student_id=student.id,
            visit_date=visit_date,
            chief_complaint='Medical clearance for sports',
            diagnosis='General health check - All systems normal',
            treatment='Patient cleared for physical activities',
            status='completed'
        )
        db.session.add(visit)
        db.session.commit()
        print(f"   ✓ Created completed visit dated {visit_date}")
    else:
        print(f"\n✓ Found existing completed visit from {existing_visit.visit_date}")
    
    # Check if certificate already exists
    existing_cert = HealthCertificate.query.filter_by(student_id=student.id).first()
    if existing_cert:
        print(f"\n✓ Certificate already exists: {existing_cert.certificate_number}")
        print(f"   Purpose: {existing_cert.purpose}")
        print(f"   Valid until: {existing_cert.valid_until}")
    else:
        # Create certificate
        print("\n🏥 Creating health certificate...")
        admin = User.query.filter_by(role='admin').first()
        
        if not admin:
            print("❌ No admin found!")
            exit()
        
        cert_number = f"HC-{date.today().year}-0001"
        valid_until = date.today() + timedelta(days=180)  # 6 months
        
        certificate = HealthCertificate(
            student_id=student.id,
            issued_by=admin.id,
            certificate_number=cert_number,
            purpose='Sports Participation',
            medical_findings='General health check completed. All systems normal.\n\nPatient is fit for physical activities and sports participation.\n\nBlood Pressure: 120/80\nTemperature: 36.5°C\nHeart Rate: 72 bpm',
            valid_until=valid_until
        )
        db.session.add(certificate)
        db.session.commit()
        
        print(f"   ✓ Created certificate: {cert_number}")
        print(f"   Valid until: {valid_until.strftime('%B %d, %Y')}")
    
    print("\n" + "="*60)
    print("✅ SUCCESS! Test certificate is ready!")
    print("="*60)
    print(f"\n🔐 Login as: {student.email}")
    print("   (Check your database for the password)")
    print("\n📍 Then go to: /dashboard")
    print("   Look for 'Health Certificates' section (right column)")
    print("   Click the PDF download button")
    print("="*60)
