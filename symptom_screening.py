"""
Symptom Pre-Screening Blueprint for ISUFST CareHub.
AI-powered symptom analysis before appointment booking.
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models import db
from models_extended import SymptomScreening, AppointmentStatus
from advanced_utils import analyze_symptoms, calculate_severity_score
import json

symptom_screening = Blueprint('symptom_screening', __name__, url_prefix='/screening')


@symptom_screening.route('/')
@login_required
def index():
    """Symptom screening questionnaire."""
    if current_user.role != 'student':
        from flask import flash
        flash('Symptom screening is for students only.', 'error')
        return redirect(url_for('admin') if current_user.role in ['admin', 'nurse'] else url_for('auth.login'))
    
    return render_template('symptom_screening.html')


@symptom_screening.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """Analyze symptoms and provide recommendations."""
    data = request.get_json()
    
    symptoms = data.get('symptoms', [])
    additional_info = data.get('additional_info', '')
    
    if not symptoms:
        return jsonify({'error': 'Please select at least one symptom'}), 400
    
    # Combine symptoms for analysis
    symptoms_text = ' '.join(symptoms) + ' ' + additional_info
    
    # Analyze
    service_type, severity, suggestions = analyze_symptoms(symptoms_text)
    severity_score = calculate_severity_score(symptoms)
    
    # Save screening
    screening = SymptomScreening(
        student_id=current_user.id,
        symptoms_json=json.dumps(symptoms),
        severity_level=severity_score,
        recommended_service=service_type,
        ai_suggestions=suggestions
    )
    
    db.session.add(screening)
    db.session.commit()
    
    return jsonify({
        'screening_id': screening.id,
        'recommended_service': service_type,
        'severity': severity_score,
        'severity_label': {1: 'Emergency', 2: 'Urgent', 3: 'Routine'}.get(severity_score, 'Routine'),
        'suggestions': suggestions,
        'should_book': severity_score > 1
    })


@symptom_screening.route('/history')
@login_required
def history():
    """View previous symptom screenings."""
    if current_user.role != 'student':
        return redirect(url_for('admin') if current_user.role in ['admin', 'nurse'] else url_for('auth.login'))
    
    screenings = SymptomScreening.query.filter_by(
        student_id=current_user.id
    ).order_by(SymptomScreening.created_at.desc()).limit(10).all()
    
    return render_template('symptom_history.html', screenings=screenings)


# Symptom checklist data
SYMPTOM_CATEGORIES = {
    'General': [
        'Fever', 'Chills', 'Fatigue', 'Weakness', 'Weight loss', 'Night sweats'
    ],
    'Respiratory': [
        'Cough', 'Shortness of breath', 'Sore throat', 'Runny nose', 'Congestion'
    ],
    'Gastrointestinal': [
        'Nausea', 'Vomiting', 'Diarrhea', 'Constipation', 'Abdominal pain', 'Loss of appetite'
    ],
    'Neurological': [
        'Headache', 'Dizziness', 'Confusion', 'Memory problems', 'Numbness', 'Tingling'
    ],
    'Musculoskeletal': [
        'Muscle pain', 'Joint pain', 'Back pain', 'Neck pain', 'Stiffness'
    ],
    'Skin': [
        'Rash', 'Itching', 'Swelling', 'Bruising', 'Skin lesions'
    ],
    'Dental': [
        'Toothache', 'Gum bleeding', 'Jaw pain', 'Sensitivity'
    ],
    'Mental Health': [
        'Anxiety', 'Depression', 'Stress', 'Mood changes', 'Sleep problems'
    ]
}


@symptom_screening.route('/api/symptom-categories')
def get_symptom_categories():
    """Get symptom checklist."""
    return jsonify(SYMPTOM_CATEGORIES)
