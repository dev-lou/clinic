"""
Seed Data Script for ISUFST CareHub Clinic Management System.
Run with: python seed_data.py

Creates realistic demo data:
- 10 Filipino student accounts
- 15 Philippine medicines in inventory
- ~30 appointments (last 30 days)
- ~25 clinic visits with feedback
- Symptom screenings
- Medicine reservations
- Logbook entries
"""
import os
import sys
import json
import random
from datetime import datetime, timezone, date, timedelta, time
from dotenv import load_dotenv

load_dotenv()

# Add current directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, StudentProfile, Appointment, ClinicVisit, Inventory, MedicineReservation, MedicationLog, LogbookEntry, Notification
from models_extended import VisitFeedback, SymptomScreening
from werkzeug.security import generate_password_hash

# ──────────────────────────────────────────────
#  Configuration
# ──────────────────────────────────────────────
DEFAULT_PASSWORD = 'password123'

# Filipino student data
STUDENTS = [
    {'first_name': 'Maria', 'last_name': 'Santos', 'email': 'maria.santos@isufst.edu.ph', 'student_id': '2024-0001', 'course': 'BS Information Technology', 'year': 2, 'blood_type': 'A+', 'contact': '09171234501'},
    {'first_name': 'Juan', 'last_name': 'Dela Cruz', 'email': 'juan.delacruz@isufst.edu.ph', 'student_id': '2024-0002', 'course': 'BS Computer Science', 'year': 3, 'blood_type': 'O+', 'contact': '09171234502'},
    {'first_name': 'Ana', 'last_name': 'Reyes', 'email': 'ana.reyes@isufst.edu.ph', 'student_id': '2024-0003', 'course': 'BS Nursing', 'year': 1, 'blood_type': 'B+', 'contact': '09171234503'},
    {'first_name': 'Jose', 'last_name': 'Garcia', 'email': 'jose.garcia@isufst.edu.ph', 'student_id': '2024-0004', 'course': 'BS Business Administration', 'year': 4, 'blood_type': 'AB+', 'contact': '09171234504'},
    {'first_name': 'Carla', 'last_name': 'Villanueva', 'email': 'carla.villanueva@isufst.edu.ph', 'student_id': '2024-0005', 'course': 'BS Medical Technology', 'year': 2, 'blood_type': 'O-', 'contact': '09171234505'},
    {'first_name': 'Miguel', 'last_name': 'Torres', 'email': 'miguel.torres@isufst.edu.ph', 'student_id': '2024-0006', 'course': 'BS Information Technology', 'year': 1, 'blood_type': 'A-', 'contact': '09171234506'},
    {'first_name': 'Isabella', 'last_name': 'Mendoza', 'email': 'isabella.mendoza@isufst.edu.ph', 'student_id': '2024-0007', 'course': 'BS Education', 'year': 3, 'blood_type': 'B-', 'contact': '09171234507'},
    {'first_name': 'Rafael', 'last_name': 'Aquino', 'email': 'rafael.aquino@isufst.edu.ph', 'student_id': '2024-0008', 'course': 'BS Computer Science', 'year': 2, 'blood_type': 'O+', 'contact': '09171234508'},
    {'first_name': 'Sofia', 'last_name': 'Ramos', 'email': 'sofia.ramos@isufst.edu.ph', 'student_id': '2024-0009', 'course': 'BS Nursing', 'year': 4, 'blood_type': 'A+', 'contact': '09171234509'},
    {'first_name': 'Gabriel', 'last_name': 'Fernandez', 'email': 'gabriel.fernandez@isufst.edu.ph', 'student_id': '2024-0010', 'course': 'BS Medical Technology', 'year': 1, 'blood_type': 'AB-', 'contact': '09171234510'},
]

# Philippine medicines inventory
MEDICINES = [
    {'name': 'Paracetamol (Biogesic) 500mg', 'batch': 'BIO-2025-001', 'expiry': date(2026, 12, 31), 'qty': 500, 'category': 'Medicine'},
    {'name': 'Ibuprofen (Advil) 400mg', 'batch': 'ADV-2025-002', 'expiry': date(2026, 6, 30), 'qty': 300, 'category': 'Medicine'},
    {'name': 'Amoxicillin 500mg Capsule', 'batch': 'AMX-2025-003', 'expiry': date(2027, 3, 15), 'qty': 200, 'category': 'Medicine'},
    {'name': 'Mefenamic Acid (Dolfenal) 500mg', 'batch': 'DOL-2025-004', 'expiry': date(2026, 9, 30), 'qty': 250, 'category': 'Medicine'},
    {'name': 'Cetirizine (Virlix) 10mg', 'batch': 'VIR-2025-005', 'expiry': date(2026, 11, 30), 'qty': 400, 'category': 'Medicine'},
    {'name': 'Loperamide (Diatabs) 2mg', 'batch': 'DIA-2025-006', 'expiry': date(2026, 8, 31), 'qty': 150, 'category': 'Medicine'},
    {'name': 'Oral Rehydration Salts (ORS)', 'batch': 'ORS-2025-007', 'expiry': date(2027, 12, 31), 'qty': 300, 'category': 'Medicine'},
    {'name': 'Multivitamins (Enervon-C)', 'batch': 'ENV-2025-008', 'expiry': date(2027, 6, 30), 'qty': 350, 'category': 'Medicine'},
    {'name': 'Antacid (Kremil-S) Chewable', 'batch': 'KRM-2025-009', 'expiry': date(2026, 4, 30), 'qty': 200, 'category': 'Medicine'},
    {'name': 'Carbocisteine (Solmux) 500mg', 'batch': 'SLM-2025-010', 'expiry': date(2026, 7, 31), 'qty': 100, 'category': 'Medicine'},
    {'name': 'Paracetamol Syrup (Tempra) 120mg/5ml', 'batch': 'TMP-2025-011', 'expiry': date(2027, 5, 31), 'qty': 100, 'category': 'Medicine'},
    {'name': 'Montelukast 10mg Tablet', 'batch': 'MNT-2025-012', 'expiry': date(2027, 8, 31), 'qty': 80, 'category': 'Medicine'},
    {'name': 'Povidone-Iodine (Betadine) 10%', 'batch': 'BTD-2025-013', 'expiry': date(2026, 10, 31), 'qty': 120, 'category': 'Medicine'},
    {'name': 'Isopropyl Alcohol 70% 500ml', 'batch': 'ALC-2025-014', 'expiry': date(2027, 12, 31), 'qty': 60, 'category': 'Medicine'},
    {'name': 'Sterile Gauze Pads 4x4', 'batch': 'GAU-2025-015', 'expiry': date(2028, 6, 30), 'qty': 200, 'category': 'Equipment'},
]

# Service types for appointments
SERVICE_TYPES = ['Medical', 'Dental', 'Mental Health', 'Laboratory', 'Physical Therapy']

# Appointment statuses with realistic distribution
STATUS_WEIGHTS = {
    'Completed': 50,
    'Confirmed': 10,
    'Pending': 10,
    'Cancelled': 15,
    'No Show': 15,
}

# Chief complaints for clinic visits
CHIEF_COMPLAINTS = [
    ('Headache', 'Tension Headache', 'Paracetamol 500mg, Rest and adequate hydration'),
    ('Fever (38.5°C)', 'Acute Febrile Illness', 'Paracetamol 500mg every 6 hours, sponge bath, increase fluid intake'),
    ('Cough and Colds', 'Upper Respiratory Tract Infection', 'Carbocisteine 500mg, Paracetamol 500mg, rest'),
    ('Stomach Ache', 'Gastritis', 'Antacid (Kremil-S), soft diet, avoid spicy food'),
    ('Allergic Reaction (Skin Rashes)', 'Allergic Dermatitis', 'Cetirizine 10mg once daily, avoid allergen'),
    ('Dizziness', 'Hypotension / Dehydration', 'ORS, rest in supine position, monitor BP'),
    ('Menstrual Cramps', 'Dysmenorrhea', 'Mefenamic Acid 500mg, warm compress on lower abdomen'),
    ('Skin Rash', 'Contact Dermatitis', 'Topical antihistamine, Cetirizine 10mg'),
    ('Toothache', 'Dental Caries', 'Referral to Dental Clinic, Paracetamol for pain'),
    ('Anxiety / Stress', 'Acute Stress Reaction', 'Rest, breathing exercises, referral to Mental Health Counselor'),
    ('Sore Throat', 'Pharyngitis', 'Warm saline gargle, Paracetamol 500mg, lozenges'),
    ('Body Weakness', 'General Fatigue', 'Multivitamins, adequate rest, balanced diet'),
    ('Nausea and Vomiting', 'Acute Gastroenteritis', 'ORS, Loperamide if diarrhea persists, soft diet'),
    ('Back Pain', 'Muscle Strain', 'Ibuprofen 400mg, warm compress, avoid heavy lifting'),
    ('Eye Irritation', 'Conjunctivitis', 'Eye drops, cold compress, avoid rubbing eyes'),
]

# Symptom screening data
SYMPTOM_SCREENINGS = [
    {'symptoms': ['Headache', 'Fever', 'Fatigue'], 'severity': 2, 'service': 'Medical'},
    {'symptoms': ['Cough', 'Sore Throat', 'Runny Nose'], 'severity': 3, 'service': 'Medical'},
    {'symptoms': ['Stomach Pain', 'Nausea', 'Diarrhea'], 'severity': 2, 'service': 'Medical'},
    {'symptoms': ['Skin Rash', 'Itching', 'Redness'], 'severity': 3, 'service': 'Medical'},
    {'symptoms': ['Anxiety', 'Insomnia', 'Stress'], 'severity': 2, 'service': 'Mental Health'},
    {'symptoms': ['Toothache', 'Swollen Gums', 'Jaw Pain'], 'severity': 3, 'service': 'Dental'},
    {'symptoms': ['Dizziness', 'Fatigue', 'Weakness'], 'severity': 3, 'service': 'Medical'},
    {'symptoms': ['Back Pain', 'Muscle Ache', 'Stiffness'], 'severity': 3, 'service': 'Physical Therapy'},
    {'symptoms': ['Allergies', 'Sneezing', 'Watery Eyes'], 'severity': 3, 'service': 'Medical'},
    {'symptoms': ['Menstrual Pain', 'Cramping', 'Headache'], 'severity': 3, 'service': 'Medical'},
]


def clear_existing_data():
    """Clear all existing demo data."""
    print('[CLEAR] Clearing existing data...')
    
    # Delete in order to respect foreign keys
    Notification.query.delete()
    LogbookEntry.query.delete()
    MedicineReservation.query.delete()
    MedicationLog.query.delete()
    VisitFeedback.query.delete()
    SymptomScreening.query.delete()
    ClinicVisit.query.delete()
    Appointment.query.delete()
    Inventory.query.delete()
    
    # Keep admin users, delete student users
    student_users = User.query.filter_by(role='student').all()
    for user in student_users:
        if user.student_profile:
            db.session.delete(user.student_profile)
        db.session.delete(user)
    
    db.session.commit()
    print('   [OK] Existing data cleared')


def create_students():
    """Create Filipino student accounts."""
    print('[STUDENTS] Creating 10 Filipino student accounts...')
    
    created = []
    for s in STUDENTS:
        # Check if already exists
        if User.query.filter_by(email=s['email']).first():
            print(f'   [WARN]  {s["email"]} already exists, skipping')
            continue
        
        user = User(
            email=s['email'],
            first_name=s['first_name'],
            last_name=s['last_name'],
            role='student',
            is_active=True,
        )
        user.password_hash = generate_password_hash(DEFAULT_PASSWORD)
        db.session.add(user)
        db.session.flush()  # Get the user ID
        
        profile = StudentProfile(
            user_id=user.id,
            student_id_number=s['student_id'],
            course=s['course'],
            year_level=s['year'],
            contact_number=s['contact'],
            blood_type=s['blood_type'],
            emergency_contact_name=f"Parent of {s['first_name']}",
            emergency_contact_number=f"0917999{random.randint(1000, 9999)}",
            allergies='None' if random.random() > 0.2 else random.choice(['Penicillin', 'Seafood', 'Dust']),
            medical_conditions='None' if random.random() > 0.3 else random.choice(['Asthma', 'Allergic Rhinitis', 'Migraine']),
        )
        db.session.add(profile)
        created.append(user)
    
    db.session.commit()
    print(f'   [OK] Created {len(created)} student accounts')
    return created


def create_medicines():
    """Add Philippine medicines to inventory."""
    print('[MEDICINES] Adding 15 Philippine medicines to inventory...')
    
    created = []
    for med in MEDICINES:
        # Check if already exists
        if Inventory.query.filter_by(name=med['name']).first():
            print(f'   [WARN]  {med["name"]} already exists, skipping')
            continue
        
        item = Inventory(
            name=med['name'],
            batch_number=med['batch'],
            expiry_date=med['expiry'],
            quantity=med['qty'],
            category=med['category'],
        )
        db.session.add(item)
        created.append(item)
    
    db.session.commit()
    print(f'   [OK] Added {len(created)} items to inventory')
    return created


def create_appointments(students):
    """Create appointments over the last 30 days."""
    print('[APPOINTMENTS] Creating appointments (last 30 days)...')
    
    created = []
    today = date.today()
    
    for i in range(30):
        days_ago = random.randint(0, 29)
        appt_date = today - timedelta(days=days_ago)
        
        # Skip weekends sometimes
        if appt_date.weekday() >= 5 and random.random() > 0.3:
            continue
        
        student = random.choice(students)
        service = random.choice(SERVICE_TYPES)
        
        # Random time slot (8 AM - 5 PM)
        hour = random.randint(8, 16)
        minute = random.choice([0, 15, 30, 45])
        start_time = time(hour, minute)
        end_time = time(hour, (minute + 30) % 60) if minute < 30 else time(hour + 1, 0)
        
        # Weighted status
        status_choices = list(STATUS_WEIGHTS.keys())
        weights = list(STATUS_WEIGHTS.values())
        status = random.choices(status_choices, weights=weights, k=1)[0]
        
        # Future appointments should be Pending or Confirmed
        if days_ago <= 0:
            status = random.choice(['Pending', 'Confirmed'])
        
        # Check for duplicate
        existing = Appointment.query.filter_by(
            student_id=student.id,
            appointment_date=appt_date,
            service_type=service
        ).first()
        if existing:
            continue
        
        appt = Appointment(
            student_id=student.id,
            service_type=service,
            appointment_date=appt_date,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )
        db.session.add(appt)
        created.append(appt)
    
    db.session.commit()
    print(f'   [OK] Created {len(created)} appointments')
    return created


def create_visits(appointments, students):
    """Create clinic visits for completed appointments."""
    print('[VISITS] Creating clinic visits with chief complaints...')
    
    created = []
    completed_appts = [a for a in appointments if a.status == 'Completed']
    
    for appt in completed_appts:
        # Check if visit already exists
        existing = ClinicVisit.query.filter_by(
            student_id=appt.student_id,
        ).filter(
            ClinicVisit.visit_date >= datetime.combine(appt.appointment_date, time.min),
            ClinicVisit.visit_date <= datetime.combine(appt.appointment_date, time.max)
        ).first()
        if existing:
            continue
        
        complaint_data = random.choice(CHIEF_COMPLAINTS)
        
        # Randomize visit time within the appointment slot
        visit_hour = appt.start_time.hour
        visit_minute = random.randint(0, 30)
        visit_dt = datetime.combine(appt.appointment_date, time(visit_hour, visit_minute))
        visit_dt = visit_dt.replace(tzinfo=timezone.utc)
        
        visit = ClinicVisit(
            student_id=appt.student_id,
            visit_date=visit_dt,
            chief_complaint=complaint_data[0],
            diagnosis=complaint_data[1],
            treatment=complaint_data[2],
            status='completed',
            notes='Patient responded well to treatment.',
        )
        db.session.add(visit)
        created.append(visit)
    
    # Also create some walk-in visits (no appointment)
    walkin_count = max(1, len(created) // 4)
    for _ in range(walkin_count):
        student = random.choice(students)
        days_ago = random.randint(1, 25)
        visit_date = date.today() - timedelta(days=days_ago)
        visit_hour = random.randint(9, 16)
        visit_dt = datetime.combine(visit_date, time(visit_hour, random.randint(0, 30)))
        visit_dt = visit_dt.replace(tzinfo=timezone.utc)
        
        complaint_data = random.choice(CHIEF_COMPLAINTS)
        
        visit = ClinicVisit(
            student_id=student.id,
            visit_date=visit_dt,
            chief_complaint=complaint_data[0],
            diagnosis=complaint_data[1],
            treatment=complaint_data[2],
            status='completed',
            notes='Walk-in patient.',
        )
        db.session.add(visit)
        created.append(visit)
    
    db.session.commit()
    print(f'   [OK] Created {len(created)} clinic visits')
    return created


def create_feedback(visits):
    """Create visit feedback ratings."""
    print('[FEEDBACK] Creating visit feedback ratings...')
    
    created = []
    rated_visits = random.sample(visits, min(len(visits), int(len(visits) * 0.8)))
    
    comments_pool = [
        'Very professional and caring staff. Thank you!',
        'Quick and efficient service. Highly recommended.',
        'The doctor was very thorough in explaining my condition.',
        'Clean facility and friendly nurses.',
        'Waited a bit long but service was good overall.',
        'Excellent care. Will definitely come back.',
        'Staff was accommodating and helpful.',
        'The clinic was well-organized and the process was smooth.',
        'Good experience overall. The doctor was knowledgeable.',
        'Very satisfied with the service.',
        'The medicine given was effective.',
        'Nurses were gentle and attentive.',
        'Fast consultation. Very efficient.',
        'The clinic needs more staff during peak hours.',
        'Great facilities and professional staff.',
    ]
    
    for visit in rated_visits:
        # Weighted ratings (more 4-5 than 1-2)
        rating = random.choices([5, 4, 3, 2, 1], weights=[35, 35, 20, 7, 3], k=1)[0]
        
        existing = VisitFeedback.query.filter_by(visit_id=visit.id).first()
        if existing:
            continue
        
        feedback = VisitFeedback(
            visit_id=visit.id,
            student_id=visit.student_id,
            rating=rating,
            wait_time_rating=max(1, rating + random.randint(-1, 1)),
            staff_rating=max(1, rating + random.randint(0, 1)),
            facility_rating=max(1, rating + random.randint(-1, 1)),
            comments=random.choice(comments_pool),
            is_anonymous=random.random() > 0.7,
            submitted_at=visit.visit_date + timedelta(hours=random.randint(1, 24)),
        )
        db.session.add(feedback)
        created.append(feedback)
    
    db.session.commit()
    print(f'   [OK] Created {len(created)} feedback ratings')
    return created


def create_screenings(students):
    """Create symptom screenings."""
    print('[SCREENINGS] Creating symptom screenings...')
    
    created = []
    today = date.today()
    
    for screening_data in SYMPTOM_SCREENINGS:
        for _ in range(random.randint(1, 3)):  # Each screening type appears 1-3 times
            student = random.choice(students)
            days_ago = random.randint(1, 28)
            created_at = datetime.combine(
                today - timedelta(days=days_ago),
                time(random.randint(8, 17), random.randint(0, 59))
            ).replace(tzinfo=timezone.utc)
            
            # AI suggestions based on severity
            if screening_data['severity'] == 1:
                suggestion = 'Please proceed to the Emergency Room immediately for evaluation.'
            elif screening_data['severity'] == 2:
                suggestion = 'Prompt evaluation recommended. Schedule a clinic appointment within 24 hours.'
            else:
                suggestion = 'Non-urgent. Schedule an appointment at your earliest convenience through CareHub.'
            
            screening = SymptomScreening(
                student_id=student.id,
                symptoms_json=json.dumps(screening_data['symptoms']),
                severity_level=screening_data['severity'],
                recommended_service=screening_data['service'],
                ai_suggestions=suggestion,
                created_at=created_at,
            )
            db.session.add(screening)
            created.append(screening)
    
    db.session.commit()
    print(f'   [OK] Created {len(created)} symptom screenings')
    return created


def create_reservations(students):
    """Create medicine reservations."""
    print('[RESERVATIONS] Creating medicine reservations...')
    
    created = []
    medicine_names = [m['name'] for m in MEDICINES if m['category'] == 'Medicine']
    statuses = ['Reserved', 'Ready', 'Claimed', 'Cancelled']
    status_weights = [30, 25, 35, 10]
    
    for _ in range(15):
        student = random.choice(students)
        medicine = random.choice(medicine_names)
        days_ago = random.randint(1, 25)
        reserved_at = datetime.combine(
            date.today() - timedelta(days=days_ago),
            time(random.randint(8, 17), random.randint(0, 59))
        ).replace(tzinfo=timezone.utc)
        
        status = random.choices(statuses, weights=status_weights, k=1)[0]
        picked_up_at = None
        if status == 'Claimed':
            picked_up_at = reserved_at + timedelta(hours=random.randint(1, 48))
        
        existing = MedicineReservation.query.filter_by(
            student_id=student.id,
            medicine_name=medicine,
            reserved_at=reserved_at
        ).first()
        if existing:
            continue
        
        reservation = MedicineReservation(
            student_id=student.id,
            medicine_name=medicine,
            quantity=random.randint(1, 3),
            status=status,
            reserved_at=reserved_at,
            picked_up_at=picked_up_at,
        )
        db.session.add(reservation)
        created.append(reservation)
    
    db.session.commit()
    print(f'   [OK] Created {len(created)} medicine reservations')
    return created


def create_logbook(students):
    """Create logbook entries."""
    print('[LOGBOOK] Creating logbook entries...')
    
    created = []
    purposes = ['Medical', 'Medical', 'Medical', 'Dental', 'Medicine Pickup', 'Walk-in']
    today = date.today()
    
    for _ in range(20):
        student = random.choice(students)
        days_ago = random.randint(0, 28)
        check_in_date = today - timedelta(days=days_ago)
        
        # Skip weekends
        if check_in_date.weekday() >= 5:
            continue
        
        check_in_hour = random.randint(8, 16)
        check_in_minute = random.randint(0, 59)
        check_in = datetime.combine(check_in_date, time(check_in_hour, check_in_minute)).replace(tzinfo=timezone.utc)
        
        # Check-out 30-90 minutes later
        duration = random.randint(30, 90)
        check_out = check_in + timedelta(minutes=duration)
        
        purpose = random.choice(purposes)
        
        existing = LogbookEntry.query.filter_by(
            student_id=student.id,
            check_in_time=check_in
        ).first()
        if existing:
            continue
        
        entry = LogbookEntry(
            student_id=student.id,
            student_name=f'{student.first_name} {student.last_name}',
            student_number=student.student_profile.student_id_number if student.student_profile else '',
            purpose=purpose,
            check_in_time=check_in,
            check_out_time=check_out,
            status='Completed',
            notes='',
        )
        db.session.add(entry)
        created.append(entry)
    
    db.session.commit()
    print(f'   [OK] Created {len(created)} logbook entries')
    return created


def main():
    """Main seed function."""
    print('=' * 50)
    print('[SEED] ISUFST CareHub - Database Seed Script')
    print('=' * 50)
    print()
    
    app = create_app()
    
    with app.app_context():
        # Clear existing data
        clear_existing_data()
        print()
        
        # Create data in order
        students = create_students()
        medicines = create_medicines()
        appointments = create_appointments(students)
        visits = create_visits(appointments, students)
        feedback = create_feedback(visits)
        screenings = create_screenings(students)
        reservations = create_reservations(students)
        logbook = create_logbook(students)
        
        print()
        print('=' * 50)
        print('[OK] Seed data created successfully!')
        print('=' * 50)
        print()
        print('Summary:')
        print(f'  [STUDENTS] Students: {len(students)}')
        print(f'  [MEDICINES] Medicines: {len(medicines)}')
        print(f'  [APPOINTMENTS] Appointments: {len(appointments)}')
        print(f'  [VISITS] Visits: {len(visits)}')
        print(f'  [FEEDBACK] Feedback: {len(feedback)}')
        print(f'  [SCREENINGS] Screenings: {len(screenings)}')
        print(f'  [RESERVATIONS] Reservations: {len(reservations)}')
        print(f'  [LOGBOOK] Logbook: {len(logbook)}')
        print()
        print('Default student password: password123')
        print('Login as admin to see the populated dashboard & analytics.')
        print()


if __name__ == '__main__':
    main()
