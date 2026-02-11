"""
REST API v1 for ISUFST CareHub.
Provides JSON API for mobile app and third-party integrations.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash
from models import db, User, Appointment, ClinicVisit, Inventory, MedicineReservation, Notification
from models_extended import AppointmentWaitlist, VisitFeedback, HealthCertificate
from datetime import datetime, date, time
from functools import wraps

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')


# ──────────────────────────────────────────────
#  API Authentication
# ──────────────────────────────────────────────

def api_required(f):
    """Decorator for API authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def student_only(f):
    """Decorator to restrict to students."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'student':
            return jsonify({'error': 'Students only'}), 403
        return f(*args, **kwargs)
    return decorated_function


def staff_only(f):
    """Decorator to restrict to staff."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['nurse', 'doctor', 'admin']:
            return jsonify({'error': 'Staff only'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ──────────────────────────────────────────────
#  Authentication Endpoints
# ──────────────────────────────────────────────

@api_v1.route('/auth/login', methods=['POST'])
def login():
    """API login endpoint."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is inactive'}), 403
    
    # In a production API, you would return a JWT token here
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role
        }
    })


@api_v1.route('/auth/me')
@api_required
def me():
    """Get current user info."""
    user_data = {
        'id': current_user.id,
        'email': current_user.email,
        'first_name': current_user.first_name,
        'last_name': current_user.last_name,
        'role': current_user.role,
        'is_active': current_user.is_active
    }
    
    if current_user.role == 'student' and current_user.student_profile:
        profile = current_user.student_profile
        user_data['profile'] = {
            'student_id_number': profile.student_id_number,
            'course': profile.course,
            'year_level': profile.year_level,
            'contact_number': profile.contact_number,
            'blood_type': profile.blood_type
        }
    
    return jsonify(user_data)


# ──────────────────────────────────────────────
#  Appointment Endpoints
# ──────────────────────────────────────────────

@api_v1.route('/appointments', methods=['GET'])
@api_required
@student_only
def get_appointments():
    """Get all appointments for current student."""
    appointments = Appointment.query.filter_by(
        student_id=current_user.id
    ).order_by(Appointment.appointment_date.desc()).all()
    
    return jsonify([{
        'id': appt.id,
        'service_type': appt.service_type,
        'appointment_date': appt.appointment_date.isoformat(),
        'start_time': appt.start_time.strftime('%H:%M'),
        'end_time': appt.end_time.strftime('%H:%M'),
        'status': appt.status,
        'created_at': appt.created_at.isoformat()
    } for appt in appointments])


@api_v1.route('/appointments/<int:id>', methods=['GET'])
@api_required
def get_appointment(id):
    """Get specific appointment details."""
    appt = Appointment.query.get_or_404(id)
    
    # Verify access
    if current_user.role == 'student' and appt.student_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'id': appt.id,
        'service_type': appt.service_type,
        'appointment_date': appt.appointment_date.isoformat(),
        'start_time': appt.start_time.strftime('%H:%M'),
        'end_time': appt.end_time.strftime('%H:%M'),
        'status': appt.status,
        'created_at': appt.created_at.isoformat()
    })


@api_v1.route('/appointments', methods=['POST'])
@api_required
@student_only
def book_appointment():
    """Book a new appointment."""
    data = request.get_json()
    
    required_fields = ['service_type', 'appointment_date', 'start_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        appt_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data.get('end_time', ''), '%H:%M').time() if data.get('end_time') else \
                   (datetime.combine(date.today(), start_time) + timedelta(minutes=30)).time()
    except ValueError:
        return jsonify({'error': 'Invalid date/time format'}), 400
    
    # Create appointment
    appointment = Appointment(
        student_id=current_user.id,
        service_type=data['service_type'],
        appointment_date=appt_date,
        start_time=start_time,
        end_time=end_time,
        status='Pending'
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'appointment_id': appointment.id,
        'message': 'Appointment booked successfully'
    }), 201


@api_v1.route('/appointments/<int:id>/cancel', methods=['POST'])
@api_required
def cancel_appointment(id):
    """Cancel an appointment."""
    appt = Appointment.query.get_or_404(id)
    
    # Verify access
    if current_user.role == 'student' and appt.student_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    appt.status = 'Cancelled'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Appointment cancelled'
    })


@api_v1.route('/appointments/availability', methods=['GET'])
@api_required
def check_availability():
    """Check available slots for a date."""
    date_str = request.args.get('date')
    service_type = request.args.get('service_type', 'Medical')
    
    if not date_str:
        return jsonify({'error': 'date parameter required'}), 400
    
    try:
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)'}), 400
    
    # Generate slots and check availability
    from datetime import timedelta
    slots = []
    current = datetime.strptime('09:00', '%H:%M')
    end = datetime.strptime('17:00', '%H:%M')
    
    while current < end:
        slot_time = current.time()
        
        # Count bookings
        booked = Appointment.query.filter(
            Appointment.appointment_date == check_date,
            Appointment.start_time == slot_time,
            Appointment.status.in_(['Pending', 'Confirmed'])
        ).count()
        
        slots.append({
            'time': current.strftime('%H:%M'),
            'available': booked < 3,
            'booked_count': booked
        })
        
        current += timedelta(minutes=30)
    
    return jsonify({
        'date': date_str,
        'service_type': service_type,
        'slots': slots
    })


# ──────────────────────────────────────────────
#  Medical Records Endpoints
# ──────────────────────────────────────────────

@api_v1.route('/medical-records', methods=['GET'])
@api_required
@student_only
def get_medical_records():
    """Get medical history for current student."""
    visits = ClinicVisit.query.filter_by(
        student_id=current_user.id
    ).order_by(ClinicVisit.visit_date.desc()).all()
    
    return jsonify([{
        'id': visit.id,
        'visit_date': visit.visit_date.isoformat(),
        'chief_complaint': visit.chief_complaint,
        'diagnosis': visit.diagnosis,
        'treatment': visit.treatment,
        'status': visit.status
    } for visit in visits])


# ──────────────────────────────────────────────
#  Medicine & Inventory Endpoints
# ──────────────────────────────────────────────

@api_v1.route('/medicines', methods=['GET'])
@api_required
def get_medicines():
    """Get available medicines."""
    medicines = Inventory.query.filter(
        Inventory.category == 'Medicine',
        Inventory.quantity > 0
    ).all()
    
    return jsonify([{
        'id': med.id,
        'name': med.name,
        'quantity': med.quantity,
        'expiry_date': med.expiry_date.isoformat() if med.expiry_date else None
    } for med in medicines])


@api_v1.route('/reservations', methods=['GET'])
@api_required
@student_only
def get_reservations():
    """Get medicine reservations for current student."""
    reservations = MedicineReservation.query.filter_by(
        student_id=current_user.id
    ).order_by(MedicineReservation.reserved_at.desc()).all()
    
    return jsonify([{
        'id': res.id,
        'medicine_name': res.medicine_name,
        'quantity': res.quantity,
        'status': res.status,
        'reserved_at': res.reserved_at.isoformat(),
        'picked_up_at': res.picked_up_at.isoformat() if res.picked_up_at else None
    } for res in reservations])


@api_v1.route('/reservations', methods=['POST'])
@api_required
@student_only
def create_reservation():
    """Create a new medicine reservation."""
    data = request.get_json()
    
    if not data.get('medicine_name') or not data.get('quantity'):
        return jsonify({'error': 'medicine_name and quantity required'}), 400
    
    reservation = MedicineReservation(
        student_id=current_user.id,
        medicine_name=data['medicine_name'],
        quantity=data['quantity'],
        status='Reserved'
    )
    
    db.session.add(reservation)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'reservation_id': reservation.id
    }), 201


# ──────────────────────────────────────────────
#  Notification Endpoints
# ──────────────────────────────────────────────

@api_v1.route('/notifications', methods=['GET'])
@api_required
def get_notifications():
    """Get notifications for current user."""
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
    
    return jsonify([{
        'id': notif.id,
        'type': notif.type,
        'title': notif.title,
        'message': notif.message,
        'link': notif.link,
        'is_read': notif.is_read,
        'created_at': notif.created_at.isoformat()
    } for notif in notifications])


@api_v1.route('/notifications/<int:id>/read', methods=['POST'])
@api_required
def mark_notification_read(id):
    """Mark notification as read."""
    notif = Notification.query.get_or_404(id)
    
    if notif.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notif.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})


# ──────────────────────────────────────────────
#  Feedback Endpoints
# ──────────────────────────────────────────────

@api_v1.route('/feedback', methods=['POST'])
@api_required
@student_only
def submit_feedback():
    """Submit feedback for a visit."""
    data = request.get_json()
    
    if not data.get('visit_id') or not data.get('rating'):
        return jsonify({'error': 'visit_id and rating required'}), 400
    
    # Verify the visit belongs to the student
    visit = ClinicVisit.query.get_or_404(data['visit_id'])
    if visit.student_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if feedback already exists
    existing = VisitFeedback.query.filter_by(visit_id=data['visit_id']).first()
    if existing:
        return jsonify({'error': 'Feedback already submitted'}), 400
    
    feedback = VisitFeedback(
        visit_id=data['visit_id'],
        student_id=current_user.id,
        rating=data['rating'],
        wait_time_rating=data.get('wait_time_rating'),
        staff_rating=data.get('staff_rating'),
        facility_rating=data.get('facility_rating'),
        comments=data.get('comments'),
        is_anonymous=data.get('is_anonymous', False)
    )
    
    db.session.add(feedback)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Thank you for your feedback!'
    }), 201


# ──────────────────────────────────────────────
#  Health Summary
# ──────────────────────────────────────────────

@api_v1.route('/health-summary', methods=['GET'])
@api_required
@student_only
def health_summary():
    """Get comprehensive health summary for student."""
    total_visits = ClinicVisit.query.filter_by(student_id=current_user.id).count()
    total_appointments = Appointment.query.filter_by(student_id=current_user.id).count()
    active_reservations = MedicineReservation.query.filter_by(
        student_id=current_user.id,
        status='Reserved'
    ).count()
    
    upcoming_appointments = Appointment.query.filter(
        Appointment.student_id == current_user.id,
        Appointment.appointment_date >= date.today(),
        Appointment.status.in_(['Pending', 'Confirmed'])
    ).order_by(Appointment.appointment_date, Appointment.start_time).limit(3).all()
    
    return jsonify({
        'statistics': {
            'total_visits': total_visits,
            'total_appointments': total_appointments,
            'active_reservations': active_reservations
        },
        'upcoming_appointments': [{
            'id': appt.id,
            'service_type': appt.service_type,
            'date': appt.appointment_date.isoformat(),
            'time': appt.start_time.strftime('%H:%M')
        } for appt in upcoming_appointments]
    })
