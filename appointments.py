"""
Appointments blueprint for ISUFST CareHub.
Handles appointment booking, viewing, and cancellation.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, time, timedelta
import calendar
from models import db, Appointment, User
from utils import check_availability
from sqlalchemy import func

appointments = Blueprint('appointments', __name__, url_prefix='/appointments')

# Time slot configuration
CLINIC_START_HOUR = 9
CLINIC_END_HOUR = 17
SLOT_DURATION_MINUTES = 30
MAX_APPOINTMENTS_PER_SLOT = {
    'Dental': 2,
    'Medical': 3
}

def generate_time_slots():
    """Generate all available time slots for a day in 12-hour format."""
    slots = []
    current = datetime.strptime(f'{CLINIC_START_HOUR}:00', '%H:%M')
    end = datetime.strptime(f'{CLINIC_END_HOUR}:00', '%H:%M')
    
    while current < end:
        # Store both 24-hour value and 12-hour display
        slot_24h = current.strftime('%H:%M')
        slot_12h = current.strftime('%I:%M %p')
        slots.append({'value': slot_24h, 'display': slot_12h})
        current += timedelta(minutes=SLOT_DURATION_MINUTES)
    
    return slots


@appointments.route('/check-availability')
@login_required
def check_availability_api():
    """API endpoint to check slot availability for a specific date and service."""
    date_str = request.args.get('date')
    service_type = request.args.get('service', 'Medical')
    
    if not date_str:
        return jsonify({'error': 'Date is required'}), 400
    
    try:
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Get all appointments for this date and service
    appointments = Appointment.query.filter(
        Appointment.appointment_date == check_date,
        Appointment.service_type == service_type,
        Appointment.status.in_(['Pending', 'Confirmed'])
    ).all()
    
    # Generate time slots and check availability
    time_slots = generate_time_slots()
    available_slots = []
    
    max_per_slot = MAX_APPOINTMENTS_PER_SLOT.get(service_type, 2)
    
    for slot_dict in time_slots:
        slot_time = datetime.strptime(slot_dict['value'], '%H:%M').time()
        
        # Count appointments in this slot
        count = sum(1 for appt in appointments 
                   if appt.start_time == slot_time)
        
        available_slots.append({
            'time': slot_dict['value'],
            'available': count < max_per_slot,
            'remaining': max(0, max_per_slot - count)
        })
    
    return jsonify({
        'date': date_str,
        'service': service_type,
        'availableSlots': available_slots
    })


@appointments.route('/check-date-availability')
@login_required
def check_date_availability():
    """API endpoint to check which dates in a month are fully booked."""
    year = int(request.args.get('year', date.today().year))
    month = int(request.args.get('month', date.today().month))
    service_type = request.args.get('service', 'Medical')
    
    # Get all dates in the month
    _, days_in_month = calendar.monthrange(year, month)
    
    fully_booked_dates = []
    max_per_slot = MAX_APPOINTMENTS_PER_SLOT.get(service_type, 2)
    time_slots = generate_time_slots()
    
    for day in range(1, days_in_month + 1):
        check_date = date(year, month, day)
        
        # Skip past dates
        if check_date < date.today():
            continue
        
        # Count available slots for this date
        available_count = 0
        for slot in time_slots:
            slot_time = datetime.strptime(slot['value'], '%H:%M').time()
            existing_count = Appointment.query.filter(
                Appointment.appointment_date == check_date,
                Appointment.start_time == slot_time,
                Appointment.service_type == service_type,
                Appointment.status.in_(['Pending', 'Confirmed'])
            ).count()
            
            if existing_count < max_per_slot:
                available_count += 1
        
        # If no slots available, mark as fully booked
        if available_count == 0:
            fully_booked_dates.append(check_date.strftime('%Y-%m-%d'))
    
    return jsonify({
        'year': year,
        'month': month,
        'service': service_type,
        'fullyBookedDates': fully_booked_dates
    })


@appointments.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    """Appointment booking page and form handler."""
    # Allow all logged-in users for testing
    # if current_user.role != 'student':
    #     flash('Only students can book appointments.', 'error')
    #     return redirect(url_for('index'))
    
    if request.method == 'POST':
        service_type = request.form.get('service_type')
        appointment_date_str = request.form.get('appointment_date')
        time_slot_str = request.form.get('time_slot')
        
        # Parse date and time
        try:
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(time_slot_str, '%H:%M').time()
            end_time = (datetime.strptime(time_slot_str, '%H:%M') + timedelta(minutes=SLOT_DURATION_MINUTES)).time()
        except ValueError:
            flash('Invalid date or time format.', 'error')
            return render_template('book_appointment.html')
        
        # Check if date is in the past
        if appointment_date < date.today():
            flash('Cannot book appointments in the past.', 'error')
            return render_template('book_appointment.html')
        
        # Check slot availability
        max_per_slot = MAX_APPOINTMENTS_PER_SLOT.get(service_type, 2)
        existing_count = Appointment.query.filter(
            Appointment.appointment_date == appointment_date,
            Appointment.start_time == start_time,
            Appointment.service_type == service_type,
            Appointment.status.in_(['Pending', 'Confirmed'])
        ).count()
        
        if existing_count >= max_per_slot:
            flash('This time slot is fully booked. Please choose another.', 'error')
            return render_template('book_appointment.html')
        
        # Create appointment
        appointment = Appointment(
            student_id=current_user.id,
            service_type=service_type,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            status='Pending'
        )
        db.session.add(appointment)
        db.session.commit()
        
        flash(f'✅ Appointment booked successfully for {appointment_date.strftime("%B %d, %Y")} at {start_time.strftime("%I:%M %p")}!', 'success')
        return redirect(url_for('appointments.my_appointments'))
    
    return render_template('book_appointment.html', 
                         time_slots=generate_time_slots(),
                         min_date=(date.today() + timedelta(days=1)).strftime('%Y-%m-%d'))


@appointments.route('/my')
@login_required
def my_appointments():
    """View current user's appointments."""
    # Allow all logged-in users for testing
    # if current_user.role != 'student':
    #     flash('Only students can view appointments.', 'error')
    #     return redirect(url_for('index'))
    
    # Get all appointments for this student
    upcoming = Appointment.query.filter(
        Appointment.student_id == current_user.id,
        Appointment.appointment_date >= date.today(),
        Appointment.status.in_(['Pending', 'Confirmed'])
    ).order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc()).all()
    
    past = Appointment.query.filter(
        Appointment.student_id == current_user.id,
        Appointment.appointment_date < date.today()
    ).order_by(Appointment.appointment_date.desc()).limit(10).all()
    
    completed = Appointment.query.filter(
        Appointment.student_id == current_user.id,
        Appointment.status == 'Completed'
    ).order_by(Appointment.appointment_date.desc()).limit(10).all()
    
    return render_template('my_appointments.html', upcoming=upcoming, past=past, completed=completed)


@appointments.route('/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel(appointment_id):
    """Cancel an appointment."""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check ownership
    if appointment.student_id != current_user.id:
        flash('You can only cancel your own appointments.', 'error')
        return redirect(url_for('appointments.my_appointments'))
    
    # Check if cancellable
    if appointment.status not in ['Pending', 'Confirmed']:
        flash('This appointment cannot be cancelled.', 'error')
        return redirect(url_for('appointments.my_appointments'))
    
    appointment.status = 'Cancelled'
    db.session.commit()
    
    flash('Appointment cancelled successfully.', 'success')
    return redirect(url_for('appointments.my_appointments'))


# API Endpoints
@appointments.route('/api/check-availability', methods=['POST'])
@login_required
def api_check_availability():
    """AJAX endpoint to check time slot availability."""
    data = request.get_json()
    
    try:
        appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        service_type = data['service_type']
        
        available = check_availability(appointment_date, start_time, end_time, service_type)
        
        return jsonify({'available': available})
    except (KeyError, ValueError) as e:
        return jsonify({'error': 'Invalid data'}), 400


# ═══════════ ADMIN ROUTES ═══════════
def require_staff(f):
    """Decorator to require nurse or admin role."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['nurse', 'admin']:
            flash('Access denied. Staff only.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@appointments.route('/admin')
@login_required
@require_staff
def admin_list():
    """Admin view to manage all appointments."""
    filter_status = request.args.get('status', 'all')
    filter_date = request.args.get('date')
    
    query = Appointment.query
    
    if filter_status != 'all':
        query = query.filter_by(status=filter_status)
    
    if filter_date:
        try:
            filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
            query = query.filter_by(appointment_date=filter_date_obj)
        except ValueError:
            pass
    
    appointments_list = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.start_time.desc()
    ).all()
    
    return render_template('admin_appointments.html', appointments=appointments_list, filter_status=filter_status)


@appointments.route('/admin/<int:appointment_id>/update-status', methods=['POST'])
@login_required
@require_staff
def admin_update_status(appointment_id):
    """Admin route to update appointment status."""
    appointment = Appointment.query.get_or_404(appointment_id)
    new_status = request.form.get('status')
    
    if new_status in ['Pending', 'Confirmed', 'Completed', 'Cancelled']:
        appointment.status = new_status
        db.session.commit()
        flash(f'Appointment status updated to {new_status}.', 'success')
    else:
        flash('Invalid status.', 'error')
    
    return redirect(url_for('appointments.admin_list'))
