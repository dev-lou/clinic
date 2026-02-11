"""
Analytics & Reporting Dashboard for ISUFST CareHub.
Comprehensive analytics for administration and decision-making.
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from rbac import require_permission, Permission
from models import db, Appointment, ClinicVisit, Inventory, MedicineReservation, User, Queue, StudentProfile
from models_extended import VisitFeedback, AppointmentExtended
from datetime import datetime, timedelta, date, timezone
from sqlalchemy import func, desc, extract
from collections import defaultdict
import json

analytics = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics.route('/')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def index():
    """Main analytics dashboard."""
    return render_template('analytics_dashboard.html')


@analytics.route('/api/overview')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def overview():
    """Get overview statistics."""
    today = date.today()
    this_month_start = today.replace(day=1)
    
    # Today's stats
    today_appointments = Appointment.query.filter(
        Appointment.appointment_date == today
    ).count()
    
    today_completed = Appointment.query.filter(
        Appointment.appointment_date == today,
        Appointment.status == 'Completed'
    ).count()
    
    # This month stats
    monthly_appointments = Appointment.query.filter(
        Appointment.appointment_date >= this_month_start
    ).count()
    
    monthly_visits = ClinicVisit.query.filter(
        func.date(ClinicVisit.visit_date) >= this_month_start
    ).count()
    
    # Active reservations
    active_reservations = MedicineReservation.query.filter(
        MedicineReservation.status.in_(['Reserved', 'Ready'])
    ).count()
    
    # Average satisfaction rating
    avg_rating = db.session.query(func.avg(VisitFeedback.rating)).scalar() or 0
    feedback_count = VisitFeedback.query.count()
    
    return jsonify({
        'today_appointments': today_appointments,
        'today_completed': today_completed,
        'monthly_appointments': monthly_appointments,
        'monthly_visits': monthly_visits,
        'active_reservations': active_reservations,
        'avg_satisfaction': round(float(avg_rating) if avg_rating else 0, 2),
        'feedback_count': feedback_count
    })


@analytics.route('/api/appointments-trend')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def appointments_trend():
    """Get appointment trends over time."""
    days = int(request.args.get('days', 30))
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Query appointments grouped by date
    results = db.session.query(
        Appointment.appointment_date,
        func.count(Appointment.id).label('count')
    ).filter(
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= end_date
    ).group_by(Appointment.appointment_date).all()
    
    # Fill in missing dates with 0
    date_counts = {r[0]: r[1] for r in results}
    
    labels = []
    values = []
    current = start_date
    while current <= end_date:
        labels.append(current.strftime('%b %d'))
        values.append(date_counts.get(current, 0))
        current += timedelta(days=1)
    
    return jsonify({
        'labels': labels,
        'values': values
    })


@analytics.route('/api/service-distribution')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def service_distribution():
    """Get distribution of services used."""
    results = db.session.query(
        Appointment.service_type,
        func.count(Appointment.id).label('count')
    ).filter(
        Appointment.service_type.isnot(None)
    ).group_by(Appointment.service_type).all()
    
    labels = [r[0] for r in results]
    values = [r[1] for r in results]
    
    return jsonify({
        'labels': labels,
        'values': values
    })


@analytics.route('/api/peak-hours')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def peak_hours():
    """Get peak clinic hours based on appointments."""
    # Extract hour from start_time
    results = db.session.query(
        extract('hour', Appointment.start_time).label('hour'),
        func.count(Appointment.id).label('count')
    ).filter(
        Appointment.start_time.isnot(None),
        Appointment.status.in_(['Confirmed', 'Completed'])
    ).group_by('hour').all()
    
    hour_counts = {int(r[0]): r[1] for r in results if r[0] is not None}
    
    labels = []
    values = []
    for hour in range(8, 18):  # 8 AM to 5 PM
        labels.append(f'{hour:02d}:00')
        values.append(hour_counts.get(hour, 0))
    
    return jsonify({
        'labels': labels,
        'values': values
    })


@analytics.route('/api/student-demographics')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def student_demographics():
    """Get student demographics (course, year level)."""
    # Course distribution
    course_dist = db.session.query(
        StudentProfile.course,
        func.count(User.id).label('count')
    ).join(User, StudentProfile.user_id == User.id).filter(
        User.role == 'student'
    ).group_by(StudentProfile.course).all()
    
    # Year level distribution  
    year_dist = db.session.query(
        StudentProfile.year_level,
        func.count(User.id).label('count')
    ).join(User, StudentProfile.user_id == User.id).filter(
        User.role == 'student'
    ).group_by(StudentProfile.year_level).all()
    
    return jsonify({
        'by_course': [{'course': c[0] or 'Unknown', 'count': c[1]} for c in course_dist],
        'by_year': [{'year': y[0] or 0, 'count': y[1]} for y in year_dist]
    })


@analytics.route('/api/inventory-consumption')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def inventory_consumption():
    """Track medicine consumption patterns."""
    days = int(request.args.get('days', 30))
    limit = int(request.args.get('limit', 10))
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Get reservation data as proxy for consumption
    results = db.session.query(
        MedicineReservation.medicine_name,
        func.count(MedicineReservation.id).label('count')
    ).filter(
        func.date(MedicineReservation.reserved_at) >= start_date,
        MedicineReservation.status.in_(['Claimed', 'Ready'])
    ).group_by(MedicineReservation.medicine_name).order_by(desc('count')).limit(limit).all()
    
    return jsonify([
        {'medicine_name': r[0], 'count': r[1]} for r in results
    ])


@analytics.route('/api/satisfaction-trend')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def satisfaction_trend():
    """Track satisfaction ratings over time."""
    days = int(request.args.get('days', 30))
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    results = db.session.query(
        func.date(VisitFeedback.submitted_at).label('date'),
        func.avg(VisitFeedback.rating).label('avg_rating'),
        func.count(VisitFeedback.id).label('count')
    ).filter(
        func.date(VisitFeedback.submitted_at) >= start_date
    ).group_by('date').order_by('date').all()
    
    # Fill in missing dates
    date_ratings = {r[0]: float(r[1]) for r in results}
    
    labels = []
    values = []
    current = start_date
    while current <= end_date:
        labels.append(current.strftime('%b %d'))
        values.append(round(date_ratings.get(current, 0), 2))
        current += timedelta(days=1)
    
    return jsonify({
        'labels': labels,
        'values': values
    })


@analytics.route('/api/doctor-workload')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def doctor_workload():
    """Analyze doctor and dentist workload distribution (nurses excluded as they are assistants only)."""
    results = db.session.query(
        User.first_name,
        User.last_name,
        func.count(AppointmentExtended.id).label('appointment_count')
    ).outerjoin(
        AppointmentExtended, User.id == AppointmentExtended.assigned_doctor_id
    ).filter(
        User.role.in_(['doctor']),  # Includes medical doctors and dentists (nurses are assistants only)
        User.is_active == True
    ).group_by(User.id, User.first_name, User.last_name).all()
    
    labels = [f'{r[0]} {r[1]}' for r in results]
    values = [r[2] for r in results]
    
    return jsonify({
        'labels': labels,
        'values': values
    })


@analytics.route('/api/no-show-rate')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def no_show_rate():
    """Calculate appointment no-show rate."""
    days = int(request.args.get('days', 30))
    start_date = date.today() - timedelta(days=days)
    
    total_scheduled = Appointment.query.filter(
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date < date.today()
    ).count()
    
    no_shows = Appointment.query.filter(
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date < date.today(),
        Appointment.status == 'No Show'
    ).count()
    
    rate = (no_shows / total_scheduled * 100) if total_scheduled > 0 else 0
    
    return jsonify({
        'total_scheduled': total_scheduled,
        'no_shows': no_shows,
        'rate': round(rate, 2)
    })


@analytics.route('/export/report')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def export_report():
    """Export comprehensive report as JSON/CSV."""
    format_type = request.args.get('format', 'json')
    
    report_data = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'overview': 'See /api/overview endpoint',
        'appointments_trend': 'See /api/appointments-trend endpoint',
        'service_distribution': 'See /api/service-distribution endpoint',
        'peak_hours': 'See /api/peak-hours endpoint'
    }
    
    if format_type == 'json':
        return jsonify(report_data)
    
    # TODO: Implement CSV export
    return jsonify(report_data)
