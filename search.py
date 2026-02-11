"""
Search & Filtering System for ISUFST CareHub.
Provides full-text search across patients, appointments, inventory, and records.
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from rbac import require_staff
from models import db, User, Appointment, ClinicVisit, Inventory, MedicineReservation
from sqlalchemy import or_, and_, func
from datetime import datetime

search = Blueprint('search', __name__, url_prefix='/search')


@search.route('/')
@login_required
@require_staff
def index():
    """Main search interface."""
    return render_template('search.html')


@search.route('/api/patients')
@login_required
@require_staff
def search_patients():
    """Search patients by name, email, student ID."""
    query_text = request.args.get('q', '').strip()
    
    if len(query_text) < 2:
        return jsonify([])
    
    # Search across multiple fields
    results = User.query.join(User.student_profile).filter(
        User.role == 'student',
        or_(
            func.lower(User.first_name).contains(query_text.lower()),
            func.lower(User.last_name).contains(query_text.lower()),
            func.lower(User.email).contains(query_text.lower()),
            func.lower(User.student_profile.student_id_number).contains(query_text.lower())
        )
    ).limit(20).all()
    
    return jsonify([{
        'id': user.id,
        'name': f'{user.first_name} {user.last_name}',
        'email': user.email,
        'student_id': user.student_profile.student_id_number if user.student_profile else None,
        'course': user.student_profile.course if user.student_profile else None
    } for user in results])


@search.route('/api/appointments')
@login_required
@require_staff
def search_appointments():
    """Search appointments with filters."""
    # Filters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status')
    service_type = request.args.get('service_type')
    patient_name = request.args.get('patient_name', '').strip()
    
    query = Appointment.query.join(Appointment.student)
    
    # Apply filters
    if date_from:
        query = query.filter(Appointment.appointment_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    
    if date_to:
        query = query.filter(Appointment.appointment_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    if status:
        query = query.filter(Appointment.status == status)
    
    if service_type:
        query = query.filter(Appointment.service_type == service_type)
    
    if patient_name:
        query = query.filter(
            or_(
                func.lower(User.first_name).contains(patient_name.lower()),
                func.lower(User.last_name).contains(patient_name.lower())
            )
        )
    
    appointments = query.order_by(Appointment.appointment_date.desc()).limit(50).all()
    
    return jsonify([{
        'id': appt.id,
        'patient': f'{appt.student.first_name} {appt.student.last_name}',
        'patient_id': appt.student_id,
        'service_type': appt.service_type,
        'appointment_date': appt.appointment_date.isoformat(),
        'start_time': appt.start_time.strftime('%H:%M'),
        'status': appt.status
    } for appt in appointments])


@search.route('/api/inventory')
@login_required
@require_staff
def search_inventory():
    """Search inventory items."""
    query_text = request.args.get('q', '').strip()
    category = request.args.get('category')
    low_stock_only = request.args.get('low_stock') == 'true'
    expiring_soon = request.args.get('expiring') == 'true'
    
    query = Inventory.query
    
    # Text search
    if query_text:
        query = query.filter(
            or_(
                func.lower(Inventory.name).contains(query_text.lower()),
                func.lower(Inventory.batch_number).contains(query_text.lower())
            )
        )
    
    # Category filter
    if category:
        query = query.filter(Inventory.category == category)
    
    # Low stock filter
    if low_stock_only:
        query = query.filter(Inventory.quantity < 10)
    
    # Expiring soon filter
    if expiring_soon:
        from datetime import date, timedelta
        expiry_threshold = date.today() + timedelta(days=30)
        query = query.filter(
            Inventory.expiry_date <= expiry_threshold,
            Inventory.expiry_date >= date.today()
        )
    
    items = query.order_by(Inventory.name).limit(50).all()
    
    return jsonify([{
        'id': item.id,
        'name': item.name,
        'batch_number': item.batch_number,
        'quantity': item.quantity,
        'category': item.category,
        'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None,
        'is_expiring': item.is_expiring_soon()
    } for item in items])


@search.route('/api/visits')
@login_required
@require_staff
def search_visits():
    """Search clinic visits."""
    patient_name = request.args.get('patient_name', '').strip()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    diagnosis = request.args.get('diagnosis', '').strip()
    
    query = ClinicVisit.query.join(ClinicVisit.patient)
    
    # Patient name filter
    if patient_name:
        query = query.filter(
            or_(
                func.lower(User.first_name).contains(patient_name.lower()),
                func.lower(User.last_name).contains(patient_name.lower())
            )
        )
    
    # Date range filter
    if date_from:
        query = query.filter(func.date(ClinicVisit.visit_date) >= datetime.strptime(date_from, '%Y-%m-%d').date())
    
    if date_to:
        query = query.filter(func.date(ClinicVisit.visit_date) <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    # Diagnosis filter
    if diagnosis:
        query = query.filter(func.lower(ClinicVisit.diagnosis).contains(diagnosis.lower()))
    
    visits = query.order_by(ClinicVisit.visit_date.desc()).limit(50).all()
    
    return jsonify([{
        'id': visit.id,
        'patient': f'{visit.patient.first_name} {visit.patient.last_name}',
        'visit_date': visit.visit_date.isoformat(),
        'chief_complaint': visit.chief_complaint,
        'diagnosis': visit.diagnosis,
        'status': visit.status
    } for visit in visits])


@search.route('/api/reservations')
@login_required
@require_staff
def search_reservations():
    """Search medicine reservations."""
    status = request.args.get('status')
    patient_name = request.args.get('patient_name', '').strip()
    medicine = request.args.get('medicine', '').strip()
    
    query = MedicineReservation.query.join(MedicineReservation.student)
    
    # Status filter
    if status:
        query = query.filter(MedicineReservation.status == status)
    
    # Patient filter
    if patient_name:
        query = query.filter(
            or_(
                func.lower(User.first_name).contains(patient_name.lower()),
                func.lower(User.last_name).contains(patient_name.lower())
            )
        )
    
    # Medicine filter
    if medicine:
        query = query.filter(func.lower(MedicineReservation.medicine_name).contains(medicine.lower()))
    
    reservations = query.order_by(MedicineReservation.reserved_at.desc()).limit(50).all()
    
    return jsonify([{
        'id': res.id,
        'patient': f'{res.student.first_name} {res.student.last_name}',
        'medicine': res.medicine_name,
        'quantity': res.quantity,
        'status': res.status,
        'reserved_at': res.reserved_at.isoformat()
    } for res in reservations])


@search.route('/api/global')
@login_required
@require_staff
def global_search():
    """Global search across all entities."""
    query_text = request.args.get('q', '').strip()
    
    if len(query_text) < 3:
        return jsonify({'results': []})
    
    results = {
        'patients': [],
        'appointments': [],
        'inventory': [],
        'visits': []
    }
    
    # Search patients
    patients = User.query.join(User.student_profile).filter(
        User.role == 'student',
        or_(
            func.lower(User.first_name).contains(query_text.lower()),
            func.lower(User.last_name).contains(query_text.lower()),
            func.lower(User.student_profile.student_id_number).contains(query_text.lower())
        )
    ).limit(5).all()
    
    results['patients'] = [{
        'type': 'patient',
        'id': u.id,
        'title': f'{u.first_name} {u.last_name}',
        'subtitle': u.student_profile.student_id_number if u.student_profile else None,
        'url': f'/admin/user/{u.id}'
    } for u in patients]
    
    # Search inventory
    inventory = Inventory.query.filter(
        func.lower(Inventory.name).contains(query_text.lower())
    ).limit(5).all()
    
    results['inventory'] = [{
        'type': 'medicine',
        'id': item.id,
        'title': item.name,
        'subtitle': f'{item.quantity} in stock',
        'url': f'/inventory'
    } for item in inventory]
    
    return jsonify(results)
