"""
Analytics & Reporting Dashboard for ISUFST CareHub.
Comprehensive analytics for administration and decision-making.
"""
import os
import json as json_mod
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from rbac import require_permission, Permission
from models import db, Appointment, ClinicVisit, Inventory, MedicineReservation, User, Queue, StudentProfile, Notification
from models_extended import VisitFeedback, AppointmentExtended, SymptomScreening
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


@analytics.route('/api/health-issues-trend')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def health_issues_trend():
    """Get health issues trend from symptom screenings and clinic visits."""
    days = int(request.args.get('days', 30))
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Get top symptoms from symptom screenings
    screenings = SymptomScreening.query.filter(
        SymptomScreening.created_at >= datetime.combine(start_date, datetime.min.time())
    ).all()
    
    symptom_counts = {}
    for s in screenings:
        try:
            symptoms = json_mod.loads(s.symptoms_json) if s.symptoms_json else []
            for sym in symptoms:
                symptom_counts[sym] = symptom_counts.get(sym, 0) + 1
        except:
            pass
    
    # Get top complaints from clinic visits
    visits = ClinicVisit.query.filter(
        func.date(ClinicVisit.visit_date) >= start_date,
        func.date(ClinicVisit.visit_date) <= end_date
    ).all()
    
    complaint_counts = {}
    for v in visits:
        if v.chief_complaint:
            complaint = v.chief_complaint.lower().strip()
            complaint_counts[complaint] = complaint_counts.get(complaint, 0) + 1
    
    # Combine and sort
    all_issues = {}
    for sym, count in symptom_counts.items():
        all_issues[sym] = all_issues.get(sym, 0) + count
    for comp, count in complaint_counts.items():
        all_issues[comp] = all_issues.get(comp, 0) + count
    
    # Get top 10 issues
    top_issues = sorted(all_issues.items(), key=lambda x: -x[1])[:10]
    
    return jsonify({
        'labels': [issue[0] for issue in top_issues],
        'values': [issue[1] for issue in top_issues]
    })


@analytics.route('/api/mental-health-stats')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def mental_health_stats():
    """Get mental health specific statistics."""
    days = int(request.args.get('days', 30))
    start_date = date.today() - timedelta(days=days)
    
    # Mental health appointments
    mental_appts = Appointment.query.filter(
        Appointment.appointment_date >= start_date,
        Appointment.service_type == 'Mental Health'
    ).count()
    
    # Mental health symptom screenings
    mental_screenings = SymptomScreening.query.filter(
        SymptomScreening.created_at >= datetime.combine(start_date, datetime.min.time()),
        SymptomScreening.recommended_service == 'Mental Health'
    ).count()
    
    # Total screenings for comparison
    total_screenings = SymptomScreening.query.filter(
        SymptomScreening.created_at >= datetime.combine(start_date, datetime.min.time())
    ).count()
    
    # Stress-related symptoms from screenings
    stress_keywords = ['stress', 'anxiety', 'depression', 'sleep', 'headache', 'fatigue']
    stress_count = 0
    screenings = SymptomScreening.query.filter(
        SymptomScreening.created_at >= datetime.combine(start_date, datetime.min.time())
    ).all()
    
    for s in screenings:
        try:
            symptoms = json_mod.loads(s.symptoms_json) if s.symptoms_json else []
            for sym in symptoms:
                if any(keyword in sym.lower() for keyword in stress_keywords):
                    stress_count += 1
                    break
        except:
            pass
    
    return jsonify({
        'mental_appts': mental_appts,
        'mental_screenings': mental_screenings,
        'total_screenings': total_screenings,
        'stress_related': stress_count,
        'mental_health_percentage': round((mental_appts / max(mental_appts + total_screenings - mental_screenings, 1)) * 100, 1) if total_screenings > 0 else 0
    })


@analytics.route('/api/campus-stats')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def campus_stats():
    """Get statistics grouped by campus."""
    # Define campus names (adjust based on your actual campus structure)
    campuses = ['Poblacion', 'Tiwi', 'Dumangas', 'San Enrique', 'Dingle']
    
    campus_data = []
    for campus in campuses:
        # Count appointments by campus (assuming campus info is in StudentProfile)
        # For now, we'll use a simplified approach
        appt_count = Appointment.query.filter(
            Appointment.appointment_date >= date.today() - timedelta(days=30)
        ).count()
        
        # Get visits by campus (simplified - would need campus field in models)
        visit_count = ClinicVisit.query.filter(
            func.date(ClinicVisit.visit_date) >= date.today() - timedelta(days=30)
        ).count()
        
        campus_data.append({
            'campus': campus,
            'appointments': appt_count // len(campuses),  # Simplified distribution
            'visits': visit_count // len(campuses),
            'patients': 0  # Would need actual campus data
        })
    
    return jsonify(campus_data)


@analytics.route('/api/daily-overview')
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def daily_overview():
    """Get real-time daily clinic overview."""
    today = date.today()
    
    # Today's appointments
    today_appts = Appointment.query.filter(
        Appointment.appointment_date == today
    ).count()
    
    # Today's completed appointments
    today_completed = Appointment.query.filter(
        Appointment.appointment_date == today,
        Appointment.status == 'Completed'
    ).count()
    
    # Today's no-shows
    today_no_shows = Appointment.query.filter(
        Appointment.appointment_date == today,
        Appointment.status == 'No Show'
    ).count()
    
    # Today's walk-ins (appointments without scheduled time or direct visits)
    today_visits = ClinicVisit.query.filter(
        func.date(ClinicVisit.visit_date) == today
    ).count()
    
    # Top issues today
    today_visits_data = ClinicVisit.query.filter(
        func.date(ClinicVisit.visit_date) == today
    ).all()
    
    issue_counts = {}
    for v in today_visits_data:
        if v.chief_complaint:
            complaint = v.chief_complaint.lower().strip()
            issue_counts[complaint] = issue_counts.get(complaint, 0) + 1
    
    top_issues = sorted(issue_counts.items(), key=lambda x: -x[1])[:5]
    
    # Staff on duty (simplified - count active users with nurse/doctor role)
    staff_on_duty = User.query.filter(
        User.role.in_(['nurse', 'doctor', 'admin'])
    ).count()
    
    return jsonify({
        'today_appts': today_appts,
        'today_completed': today_completed,
        'today_no_shows': today_no_shows,
        'today_visits': today_visits,
        'top_issues': [{'issue': k, 'count': v} for k, v in top_issues],
        'staff_on_duty': staff_on_duty,
        'no_show_rate': round((today_no_shows / today_appts * 100) if today_appts > 0 else 0, 1)
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


# ---------------------------------------------------------------------------
# Predictive Analytics — Gemini AI-powered
# ---------------------------------------------------------------------------
_predict_model = None

PREDICT_SYSTEM_PROMPT = """You are a healthcare analytics AI for the ISUFST University Clinic. You analyze clinic data and provide actionable predictions and insights.

RULES:
- Be data-driven and specific. Reference the numbers provided.
- Use clear, professional language suitable for clinic administrators.
- Provide actionable recommendations.
- Keep responses concise (3-5 key insights max).
- Format response as JSON with this structure:
{
  "insights": [
    {"title": "Short title", "description": "Detailed insight", "type": "warning|info|success", "icon": "fa-icon-name"}
  ],
  "summary": "One-line overall summary",
  "confidence": "high|medium|low"
}
- Return ONLY valid JSON. No markdown fences or extra text."""


import requests

class RestGeminiModel:
    def __init__(self, model_name, system_instruction):
        self.model_name = model_name
        self.system_instruction = system_instruction
        
    def generate_content(self, text):
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise RuntimeError('GEMINI_API_KEY environment variable is not set.')
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={api_key}"
        
        payload = {
            "systemInstruction": {
                "parts": [{"text": self.system_instruction}]
            },
            "contents": [
                {"parts": [{"text": text}]}
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1024,
                "responseMimeType": "application/json"
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        class RestResponse:
            def __init__(self, text):
                self.text = text
                
        try:
            content_text = data['candidates'][0]['content']['parts'][0]['text']
            return RestResponse(content_text)
        except (KeyError, IndexError) as err:
            raise ValueError(f"Unexpected response format from Gemini API: {data}") from err


def _get_predict_model():
    global _predict_model
    if _predict_model is None:
        model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
        
        # Fallback to a known working model string if the configured one is unreleased or invalid
        if "gemini-3" in model_name:
            model_name = "gemini-2.0-flash"
            
        _predict_model = RestGeminiModel(
            model_name=model_name,
            system_instruction=PREDICT_SYSTEM_PROMPT,
        )
    return _predict_model


def _clean_json_response(text):
    """Strip markdown fences from Gemini response."""
    text = text.strip()
    
    # Simple strategy: find the first { or [ and last } or ]
    start_idx = -1
    for i, char in enumerate(text):
        if char in ('{', '['):
            start_idx = i
            break
            
    end_idx = -1
    for i in range(len(text)-1, -1, -1):
        if text[i] in ('}', ']'):
            end_idx = i
            break
            
    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        return text[start_idx:end_idx+1]
        
    return text


@analytics.route('/api/predict/peak-hours', methods=['POST'])
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def predict_peak_hours():
    """AI prediction for peak clinic hours and staffing needs."""
    try:
        # Gather data
        days = 60
        start_date = date.today() - timedelta(days=days)
        results = db.session.query(
            extract('hour', Appointment.start_time).label('hour'),
            func.count(Appointment.id).label('count'),
            Appointment.service_type
        ).filter(
            Appointment.start_time.isnot(None),
            Appointment.appointment_date >= start_date,
            Appointment.status.in_(['Confirmed', 'Completed'])
        ).group_by('hour', Appointment.service_type).all()

        # Day-of-week distribution
        dow_results = db.session.query(
            extract('dow', Appointment.appointment_date).label('dow'),
            func.count(Appointment.id).label('count')
        ).filter(
            Appointment.appointment_date >= start_date,
            Appointment.status.in_(['Confirmed', 'Completed'])
        ).group_by('dow').all()

        data_summary = f"""Clinic appointment data for the past {days} days:

Hourly distribution (confirmed/completed appointments):
{chr(10).join(f'  Hour {int(r[0]):02d}:00 - {r[2]}: {r[1]} appointments' for r in results if r[0] is not None)}

Day of week distribution:
{chr(10).join(f'  Day {int(r[0])}: {r[1]} appointments' for r in dow_results if r[0] is not None)}
(0=Sunday, 1=Monday, ... 6=Saturday)

Predict: When are the busiest hours? Which days need more staff? Any patterns?"""

        model = _get_predict_model()
        response = model.generate_content(data_summary)
        result = json_mod.loads(_clean_json_response(response.text))
        return jsonify(result)
    except Exception as e:
        print(f'[Predict Peak Hours Error] {e}')
        return jsonify({'insights': [{'title': 'Analysis Unavailable', 'description': 'AI prediction is temporarily unavailable. Please try again.', 'type': 'warning', 'icon': 'fa-exclamation-triangle'}], 'summary': 'Unable to generate prediction', 'confidence': 'low'})


@analytics.route('/api/predict/medicine-demand', methods=['POST'])
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def predict_medicine_demand():
    """AI prediction for medicine demand and restocking needs."""
    try:
        # Current inventory
        inventory = Inventory.query.filter(Inventory.category == 'Medicine', Inventory.quantity > 0).all()
        inv_data = [{'name': i.name, 'quantity': i.quantity, 'expiry': str(i.expiry_date), 'batch': i.batch_number} for i in inventory]

        # Reservation trends (past 60 days)
        start_date = date.today() - timedelta(days=60)
        res_results = db.session.query(
            MedicineReservation.medicine_name,
            func.count(MedicineReservation.id).label('count')
        ).filter(
            func.date(MedicineReservation.reserved_at) >= start_date
        ).group_by(MedicineReservation.medicine_name).order_by(desc('count')).limit(15).all()

        data_summary = f"""Medicine inventory and demand data:

Current stock:
{chr(10).join(f'  {i["name"]}: {i["quantity"]} units, expires {i["expiry"]}, batch {i["batch"]}' for i in inv_data[:20])}

Reservation trends (past 60 days):
{chr(10).join(f'  {r[0]}: {r[1]} reservations' for r in res_results)}

Predict: Which medicines will run out first? Which need restocking? Any expiry concerns?"""

        model = _get_predict_model()
        response = model.generate_content(data_summary)
        result = json_mod.loads(_clean_json_response(response.text))
        return jsonify(result)
    except Exception as e:
        print(f'[Predict Medicine Error] {e}')
        return jsonify({'insights': [{'title': 'Analysis Unavailable', 'description': 'AI prediction is temporarily unavailable.', 'type': 'warning', 'icon': 'fa-exclamation-triangle'}], 'summary': 'Unable to generate prediction', 'confidence': 'low'})


@analytics.route('/api/predict/health-trends', methods=['POST'])
@login_required
@require_permission(Permission.VIEW_ANALYTICS)
def predict_health_trends():
    """AI prediction for health trends and potential outbreak detection."""
    try:
        # Symptom screening data (past 30 days)
        start_date = date.today() - timedelta(days=30)
        screenings = SymptomScreening.query.filter(
            SymptomScreening.created_at >= datetime.combine(start_date, datetime.min.time())
        ).order_by(SymptomScreening.created_at.desc()).limit(100).all()

        symptom_counts = defaultdict(int)
        service_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        for s in screenings:
            try:
                symptoms = json_mod.loads(s.symptoms_json) if s.symptoms_json else []
                for sym in symptoms:
                    symptom_counts[sym] += 1
            except Exception:
                pass
            if s.recommended_service:
                service_counts[s.recommended_service] += 1
            severity_counts[s.severity_level] += 1

        # Visit chief complaints
        visits = ClinicVisit.query.filter(
            func.date(ClinicVisit.visit_date) >= start_date
        ).all()
        complaint_counts = defaultdict(int)
        for v in visits:
            if v.chief_complaint:
                complaint_counts[v.chief_complaint.lower().strip()] += 1

        data_summary = f"""Health data for the past 30 days:

Symptom screening data ({len(screenings)} screenings):
Top reported symptoms: {', '.join(f'{k}: {v}' for k, v in sorted(symptom_counts.items(), key=lambda x: -x[1])[:15])}
Service recommendations: {', '.join(f'{k}: {v}' for k, v in service_counts.items())}
Severity distribution: Emergency: {severity_counts.get(1, 0)}, Urgent: {severity_counts.get(2, 0)}, Routine: {severity_counts.get(3, 0)}

Clinic visit data ({len(visits)} visits):
Top complaints: {', '.join(f'{k}: {v}' for k, v in sorted(complaint_counts.items(), key=lambda x: -x[1])[:10])}

Predict: Any trending symptoms suggesting an outbreak? Seasonal patterns? Concerning health trends among students?"""

        model = _get_predict_model()
        response = model.generate_content(data_summary)
        result = json_mod.loads(_clean_json_response(response.text))
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'[Predict Health Trends Error] {e}')
        return jsonify({'insights': [{'title': 'Analysis Unavailable', 'description': 'AI prediction is temporarily unavailable.', 'type': 'warning', 'icon': 'fa-exclamation-triangle'}], 'summary': 'Unable to generate prediction', 'confidence': 'low'})
