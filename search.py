"""
Search & Filtering System for ISUFST CareHub.
Provides full-text search across patients, appointments, inventory, and records.
Supports fuzzy matching for typo tolerance.
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from rbac import require_staff
from models import db, User, Appointment, ClinicVisit, Inventory, MedicineReservation, StudentProfile
from sqlalchemy import or_, and_, func
from datetime import datetime
from difflib import SequenceMatcher

search = Blueprint('search', __name__, url_prefix='/search')


def _fuzzy_score(query, text):
    """Calculate fuzzy similarity score between query and text (0.0 to 1.0)."""
    if not text or not query:
        return 0.0
    query_lower = query.lower().strip()
    text_lower = str(text).lower().strip()
    
    if not query_lower or not text_lower:
        return 0.0
    
    # Exact match or contains = best score
    if query_lower == text_lower:
        return 1.0
    if query_lower in text_lower:
        return 0.95
    
    # Check each word in text for partial match
    words = text_lower.split()
    for word in words:
        if word.startswith(query_lower):
            return 0.9
        if query_lower.startswith(word):
            return 0.85
    
    # Sequence similarity (handles typos)
    return SequenceMatcher(None, query_lower, text_lower).ratio()


def _fuzzy_search(query_text, all_items, fields, threshold=0.6):
    """Filter items by fuzzy matching query against specified fields."""
    query_lower = query_text.lower().strip()
    scored = []
    
    for item in all_items:
        best_score = 0
        for field in fields:
            val = getattr(item, field, '')
            score = _fuzzy_score(query_lower, val or '')
            if score > best_score:
                best_score = score
        if best_score >= threshold:
            scored.append((best_score, item))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


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
    """Search patients by name, email, student ID with fuzzy matching."""
    query_text = request.args.get('q', '').strip()
    
    if len(query_text) < 2:
        return jsonify([])
    
    # Try exact substring match first (fast)
    exact_results = User.query.join(StudentProfile).filter(
        User.role == 'student',
        or_(
            func.lower(User.first_name).contains(query_text.lower()),
            func.lower(User.last_name).contains(query_text.lower()),
            func.lower(User.email).contains(query_text.lower()),
            func.lower(StudentProfile.student_id_number).contains(query_text.lower())
        )
    ).limit(20).all()
    
    # If few exact results, supplement with fuzzy matching
    if len(exact_results) < 5:
        all_students = User.query.join(StudentProfile).filter(User.role == 'student').all()
        fuzzy_results = _fuzzy_search(query_text, all_students, ['first_name', 'last_name', 'email'])
        # Merge: exact first, then fuzzy (deduplicate)
        seen_ids = {u.id for u in exact_results}
        for u in fuzzy_results:
            if u.id not in seen_ids:
                exact_results.append(u)
                seen_ids.add(u.id)
    
    return jsonify([{
        'id': user.id,
        'name': f'{user.first_name} {user.last_name}',
        'email': user.email,
        'student_id': user.student_profile.student_id_number if user.student_profile else None,
        'course': user.student_profile.course if user.student_profile else None
    } for user in exact_results[:20]])


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
    """Global search across all entities with fuzzy matching."""
    query_text = request.args.get('q', '').strip()
    
    if len(query_text) < 2:
        return jsonify({'patients': [], 'inventory': []})
    
    results = {
        'patients': [],
        'inventory': []
    }
    
    # Search patients (exact match first)
    patients = User.query.join(StudentProfile).filter(
        User.role == 'student',
        or_(
            func.lower(User.first_name).contains(query_text.lower()),
            func.lower(User.last_name).contains(query_text.lower()),
            func.lower(StudentProfile.student_id_number).contains(query_text.lower())
        )
    ).limit(5).all()
    
    # Fuzzy supplement for patients
    if len(patients) < 3:
        all_students = User.query.join(StudentProfile).filter(User.role == 'student').all()
        fuzzy_patients = _fuzzy_search(query_text, all_students, ['first_name', 'last_name'])
        seen = {u.id for u in patients}
        for u in fuzzy_patients:
            if u.id not in seen:
                patients.append(u)
                seen.add(u.id)
    
    results['patients'] = [{
        'type': 'patient',
        'id': u.id,
        'title': f'{u.first_name} {u.last_name}',
        'subtitle': u.student_profile.student_id_number if u.student_profile else None,
        'url': f'/users/{u.id}/edit'
    } for u in patients[:5]]
    
    # Search inventory (exact match first)
    inventory = Inventory.query.filter(
        func.lower(Inventory.name).contains(query_text.lower())
    ).limit(5).all()
    
    # Fuzzy supplement for inventory
    if len(inventory) < 3:
        all_items = Inventory.query.all()
        fuzzy_items = _fuzzy_search(query_text, all_items, ['name'])
        seen = {i.id for i in inventory}
        for i in fuzzy_items:
            if i.id not in seen:
                inventory.append(i)
                seen.add(i.id)
    
    results['inventory'] = [{
        'type': 'medicine',
        'id': item.id,
        'title': item.name,
        'subtitle': f'{item.quantity} in stock',
        'url': f'/inventory'
    } for item in inventory[:5]]
    
    return jsonify(results)
