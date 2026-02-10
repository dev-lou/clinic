"""Test suite for utils.py functions"""
from datetime import date, time, timedelta
from app import create_app
from models import db, Appointment, Inventory, Queue, User
from utils import check_availability, dispense_medicine, get_next_patient, get_queue_summary

app = create_app()
with app.app_context():
    # Clean up test data
    db.session.query(Appointment).delete()
    db.session.query(Inventory).delete()
    db.session.query(Queue).delete()
    db.session.commit()
    
    print("=" * 60)
    print("TEST 1: check_availability()")
    print("=" * 60)
    
    # Test 1a: Empty slot should be available
    result = check_availability(date(2026, 2, 20), time(9, 0), time(10, 0), 'Dental')
    print(f"✓ Empty slot available: {result}")
    assert result == True, "Empty slot should be available"
    
    # Add an appointment
    appt = Appointment(
        student_id=1,
        service_type='Dental',
        appointment_date=date(2026, 2, 20),
        start_time=time(9, 0),
        end_time=time(10, 0),
        status='Confirmed'
    )
    db.session.add(appt)
    db.session.commit()
    
    # Test 1b: Conflicting slot should NOT be available
    result = check_availability(date(2026, 2, 20), time(9, 30), time(10, 30), 'Dental')
    print(f"✓ Conflicting Dental slot unavailable: {result}")
    assert result == False, "Overlapping Dental slot should be unavailable"
    
    # Test 1c: Different service type should be available
    result = check_availability(date(2026, 2, 20), time(9, 30), time(10, 30), 'Medical')
    print(f"✓ Different service type available: {result}")
    assert result == True, "Different service type should be available"
    
    print("\n" + "=" * 60)
    print("TEST 2: dispense_medicine() - FIFO Logic")
    print("=" * 60)
    
    # Add inventory batches with different expiry dates
    batch1 = Inventory(
        name='Paracetamol',
        batch_number='B001',
        expiry_date=date.today() + timedelta(days=30),  # Expires soonest
        quantity=10,
        category='Medicine'
    )
    batch2 = Inventory(
        name='Paracetamol',
        batch_number='B002',
        expiry_date=date.today() + timedelta(days=60),  # Expires later
        quantity=20,
        category='Medicine'
    )
    db.session.add_all([batch1, batch2])
    db.session.commit()
    
    # Test 2a: Dispense less than first batch
    result = dispense_medicine('Paracetamol', 5)
    print(f"✓ Dispensed 5 units: {result['success']}")
    print(f"  Batches used: {len(result['batches_used'])}")
    print(f"  From batch: {result['batches_used'][0]['batch_number']}")
    assert result['success'] == True
    assert result['batches_used'][0]['batch_number'] == 'B001'
    
    # Test 2b: Dispense across multiple batches
    result = dispense_medicine('Paracetamol', 15)  # 5 from B001, 10 from B002
    print(f"✓ Dispensed 15 units across batches: {result['success']}")
    print(f"  Batches used: {len(result['batches_used'])}")
    assert result['success'] == True
    assert len(result['batches_used']) == 2
    assert result['batches_used'][0]['batch_number'] == 'B001'
    assert result['batches_used'][1]['batch_number'] == 'B002'
    
    # Test 2c: Insufficient quantity
    result = dispense_medicine('Paracetamol', 100)
    print(f"✓ Insufficient quantity handled: {not result['success']}")
    assert result['success'] == False
    
    print("\n" + "=" * 60)
    print("TEST 3: get_next_patient() - Priority Sorting")
    print("=" * 60)
    
    # Add patients with different priorities
    routine = Queue(student_name='John Routine', severity_score=3, status='Waiting')
    urgent = Queue(student_name='Jane Urgent', severity_score=2, status='Waiting')
    emergency = Queue(student_name='Bob Emergency', severity_score=1, status='Waiting')
    
    db.session.add_all([routine, urgent, emergency])
    db.session.commit()
    
    # Test 3a: Emergency should be first
    next_patient = get_next_patient()
    print(f"✓ Next patient: {next_patient.student_name}")
    print(f"  Priority: {next_patient.priority_label}")
    assert next_patient.student_name == 'Bob Emergency'
    assert next_patient.severity_score == 1
    
    # Test 3b: Queue summary
    summary = get_queue_summary()
    print(f"✓ Queue summary:")
    print(f"  Total waiting: {summary['total_waiting']}")
    print(f"  Emergency: {summary['emergency']}")
    print(f"  Urgent: {summary['urgent']}")
    print(f"  Routine: {summary['routine']}")
    assert summary['total_waiting'] == 3
    assert summary['emergency'] == 1
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ✓")
    print("=" * 60)
