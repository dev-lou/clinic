"""
Patient Dashboard Blueprint for ISUFST CareHub.
Health timeline, unified view of all patient data.
"""
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Appointment, ClinicVisit, MedicineReservation, Notification
from models_extended import VisitFeedback, HealthCertificate
from datetime import datetime, timedelta
from sqlalchemy import desc

patient_dashboard = Blueprint('patient_dashboard', __name__, url_prefix='/dashboard')


@patient_dashboard.route('/')
@login_required
def index():
    """Main patient dashboard with health timeline."""
    if current_user.role != 'student':
        flash('That page is for students only.', 'error')
        return redirect(url_for('admin') if current_user.role in ['admin', 'nurse'] else url_for('auth.login'))
    
    # Upcoming appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.student_id == current_user.id,
        Appointment.appointment_date >= datetime.now().date(),
        Appointment.status.in_(['Pending', 'Confirmed'])
    ).order_by(Appointment.appointment_date, Appointment.start_time).limit(5).all()
    
    # Recent visits
    recent_visits = ClinicVisit.query.filter(
        ClinicVisit.student_id == current_user.id
    ).order_by(desc(ClinicVisit.visit_date)).limit(10).all()
    
    # Active reservations
    active_reservations = MedicineReservation.query.filter(
        MedicineReservation.student_id == current_user.id,
        MedicineReservation.status == 'Reserved'
    ).order_by(desc(MedicineReservation.reserved_at)).all()
    
    # Unread notifications
    unread_notifications = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).order_by(desc(Notification.created_at)).limit(5).all()
    
    # Health certificates
    certificates = HealthCertificate.query.filter(
        HealthCertificate.student_id == current_user.id
    ).order_by(desc(HealthCertificate.issued_at)).limit(5).all()
    
    # Pending feedback (visits without feedback)
    visits_without_feedback = db.session.query(ClinicVisit).outerjoin(
        VisitFeedback, ClinicVisit.id == VisitFeedback.visit_id
    ).filter(
        ClinicVisit.student_id == current_user.id,
        ClinicVisit.status == 'completed',
        VisitFeedback.id == None
    ).order_by(desc(ClinicVisit.visit_date)).limit(3).all()
    
    return render_template('patient_dashboard.html',
                         upcoming_appointments=upcoming_appointments,
                         recent_visits=recent_visits,
                         active_reservations=active_reservations,
                         unread_notifications=unread_notifications,
                         certificates=certificates,
                         pending_feedback=visits_without_feedback)


@patient_dashboard.route('/timeline')
@login_required
def timeline():
    """Health timeline view with all events chronologically."""
    if current_user.role != 'student':
        flash('That page is for students only.', 'error')
        return redirect(url_for('admin') if current_user.role in ['admin', 'nurse'] else url_for('auth.login'))
    
    # Combine all events into timeline
    timeline_events = []
    
    # Add appointments
    appointments = Appointment.query.filter(
        Appointment.student_id == current_user.id
    ).all()
    for appt in appointments:
        timeline_events.append({
            'date': appt.appointment_date,
            'time': appt.start_time,
            'type': 'appointment',
            'title': f'{appt.service_type} Appointment',
            'status': appt.status,
            'icon': 'calendar',
            'color': 'blue'
        })
    
    # Add visits
    visits = ClinicVisit.query.filter(
        ClinicVisit.student_id == current_user.id
    ).all()
    for visit in visits:
        timeline_events.append({
            'date': visit.visit_date.date() if isinstance(visit.visit_date, datetime) else visit.visit_date,
            'time': visit.visit_date.time() if isinstance(visit.visit_date, datetime) else None,
            'type': 'visit',
            'title': 'Clinic Visit',
            'description': visit.chief_complaint,
            'diagnosis': visit.diagnosis,
            'icon': 'heartbeat',
            'color': 'red'
        })
    
    # Add reservations
    reservations = MedicineReservation.query.filter(
        MedicineReservation.student_id == current_user.id
    ).all()
    for res in reservations:
        res_date = res.reserved_at.date() if isinstance(res.reserved_at, datetime) else res.reserved_at
        timeline_events.append({
            'date': res_date,
            'time': res.reserved_at.time() if isinstance(res.reserved_at, datetime) else None,
            'type': 'reservation',
            'title': f'Medicine: {res.medicine_name}',
            'quantity': res.quantity,
            'status': res.status,
            'icon': 'pills',
            'color': 'green'
        })
    
    # Sort by date descending
    timeline_events.sort(key=lambda x: (x['date'], x['time'] or datetime.min.time()), reverse=True)
    
    return render_template('patient_timeline.html', timeline=timeline_events)


@patient_dashboard.route('/health-stats')
@login_required
def health_stats():
    """Health statistics and trends."""
    if current_user.role != 'student':
        flash('That page is for students only.', 'error')
        return redirect(url_for('admin') if current_user.role in ['admin', 'nurse'] else url_for('auth.login'))
    
    # Count statistics
    total_visits = ClinicVisit.query.filter(
        ClinicVisit.student_id == current_user.id
    ).count()
    
    total_appointments = Appointment.query.filter(
        Appointment.student_id == current_user.id
    ).count()
    
    completed_visits = ClinicVisit.query.filter(
        ClinicVisit.student_id == current_user.id,
        ClinicVisit.status == 'completed'
    ).count()
    
    # Most common complaints (if we track vitals/complaints)
    visits = ClinicVisit.query.filter(
        ClinicVisit.student_id == current_user.id
    ).all()
    
    complaints = {}
    for visit in visits:
        if visit.chief_complaint:
            complaint = visit.chief_complaint.lower()
            complaints[complaint] = complaints.get(complaint, 0) + 1
    
    top_complaints = sorted(complaints.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return render_template('health_stats.html',
                         total_visits=total_visits,
                         total_appointments=total_appointments,
                         completed_visits=completed_visits,
                         top_complaints=top_complaints)


@patient_dashboard.route('/api/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    notification = Notification.query.get_or_404(notification_id)
    
    # Verify ownership
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})


@patient_dashboard.route('/api/notifications/unread-count')
@login_required
def unread_notification_count():
    """Get count of unread notifications."""
    count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    return jsonify({'count': count})
