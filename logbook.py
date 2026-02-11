"""
Logbook blueprint for ISUFST CareHub.
Digital clinic logbook for tracking student visits.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from datetime import datetime, date, timezone, timedelta
from models import db, LogbookEntry, User, Appointment
from functools import wraps
import csv
import io

logbook = Blueprint('logbook', __name__, url_prefix='/logbook')


def require_staff(f):
    """Decorator to require nurse or admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['nurse', 'admin']:
            flash('Access denied. Staff only.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@logbook.route('/admin')
@login_required
@require_staff
def admin_logbook():
    """Admin logbook view with filtering."""
    filter_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    filter_purpose = request.args.get('purpose', 'all')
    search = request.args.get('search', '')
    
    try:
        filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
    except ValueError:
        filter_date_obj = date.today()
    
    query = LogbookEntry.query.filter(
        db.func.date(LogbookEntry.check_in_time) == filter_date_obj
    )
    
    if filter_purpose != 'all':
        query = query.filter_by(purpose=filter_purpose)
    
    if search:
        query = query.filter(
            db.or_(
                LogbookEntry.student_name.ilike(f'%{search}%'),
                LogbookEntry.student_number.ilike(f'%{search}%')
            )
        )
    
    entries = query.order_by(LogbookEntry.check_in_time.desc()).all()
    
    # Stats for today
    today_total = LogbookEntry.query.filter(
        db.func.date(LogbookEntry.check_in_time) == date.today()
    ).count()
    
    checked_in = LogbookEntry.query.filter(
        db.func.date(LogbookEntry.check_in_time) == date.today(),
        LogbookEntry.status == 'Checked In'
    ).count()
    
    completed_today = LogbookEntry.query.filter(
        db.func.date(LogbookEntry.check_in_time) == date.today(),
        LogbookEntry.status == 'Completed'
    ).count()
    
    return render_template('admin_logbook.html',
                         entries=entries,
                         filter_date=filter_date,
                         filter_purpose=filter_purpose,
                         search=search,
                         today_total=today_total,
                         checked_in=checked_in,
                         completed_today=completed_today)


@logbook.route('/admin/check-in', methods=['POST'])
@login_required
@require_staff
def check_in():
    """Check in a student to the logbook."""
    student_id = request.form.get('student_id', type=int)
    purpose = request.form.get('purpose', 'Walk-in')
    notes = request.form.get('notes', '')
    appointment_id = request.form.get('appointment_id', type=int)
    
    if not student_id:
        flash('Please select a student.', 'error')
        return redirect(url_for('logbook.admin_logbook'))
    
    student = User.query.get(student_id)
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('logbook.admin_logbook'))
    
    entry = LogbookEntry(
        student_id=student.id,
        student_name=f'{student.first_name} {student.last_name}',
        student_number=student.student_id if hasattr(student, 'student_id') else '',
        purpose=purpose,
        appointment_id=appointment_id,
        attending_staff_id=current_user.id,
        notes=notes,
        status='Checked In'
    )
    db.session.add(entry)
    db.session.commit()
    
    flash(f'{student.first_name} {student.last_name} checked in successfully.', 'success')
    return redirect(url_for('logbook.admin_logbook'))


@logbook.route('/admin/check-out/<int:entry_id>', methods=['POST'])
@login_required
@require_staff
def check_out(entry_id):
    """Check out a student from the logbook."""
    entry = LogbookEntry.query.get_or_404(entry_id)
    entry.check_out_time = datetime.now(timezone.utc)
    entry.status = 'Completed'
    
    # Auto-complete linked appointment when logbook checked out
    if entry.appointment_id:
        appointment = Appointment.query.get(entry.appointment_id)
        if appointment and appointment.status != 'Completed':
            appointment.status = 'Completed'
    
    notes = request.form.get('notes')
    if notes:
        entry.notes = (entry.notes or '') + f'\n{notes}' if entry.notes else notes
    
    db.session.commit()
    flash(f'{entry.student_name} checked out successfully.', 'success')
    return redirect(url_for('logbook.admin_logbook'))


@logbook.route('/admin/search-students')
@login_required
@require_staff
def search_students():
    """API: Search students for check-in autocomplete."""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    students = User.query.filter(
        User.role == 'student',
        db.or_(
            (User.first_name + ' ' + User.last_name).ilike(f'%{query}%'),
            User.email.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    # Get today's appointments for each student
    results = []
    for s in students:
        today_appts = Appointment.query.filter(
            Appointment.student_id == s.id,
            Appointment.appointment_date == date.today(),
            Appointment.status.in_(['Pending', 'Confirmed'])
        ).all()
        
        results.append({
            'id': s.id,
            'name': f'{s.first_name} {s.last_name}',
            'email': s.email,
            'appointments': [{
                'id': a.id,
                'service': a.service_type,
                'time': a.start_time.strftime('%I:%M %p')
            } for a in today_appts]
        })
    
    return jsonify(results)


@logbook.route('/admin/export')
@login_required
@require_staff
def export_csv():
    """Export logbook entries to CSV."""
    start_date = request.args.get('start', date.today().strftime('%Y-%m-%d'))
    end_date = request.args.get('end', date.today().strftime('%Y-%m-%d'))
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start = end = date.today()
    
    entries = LogbookEntry.query.filter(
        db.func.date(LogbookEntry.check_in_time) >= start,
        db.func.date(LogbookEntry.check_in_time) <= end
    ).order_by(LogbookEntry.check_in_time.asc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Student Name', 'Student Number', 'Purpose', 'Check-In', 'Check-Out', 'Status', 'Staff', 'Notes'])
    
    for e in entries:
        writer.writerow([
            e.check_in_time.strftime('%Y-%m-%d') if e.check_in_time else '',
            e.student_name,
            e.student_number or '',
            e.purpose,
            e.check_in_time.strftime('%I:%M %p') if e.check_in_time else '',
            e.check_out_time.strftime('%I:%M %p') if e.check_out_time else '',
            e.status,
            e.attending_staff.full_name() if e.attending_staff else '',
            e.notes or ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=logbook_{start}_{end}.csv'}
    )
