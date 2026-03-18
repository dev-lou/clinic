"""
Symptom Pre-Screening Blueprint for ISUFST CareHub.
AI-powered symptom analysis before appointment booking.
"""
import os
import json
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models import db
from models_extended import SymptomScreening, AppointmentStatus
from advanced_utils import analyze_symptoms, calculate_severity_score

symptom_screening = Blueprint('symptom_screening', __name__, url_prefix='/screening')


@symptom_screening.route('/')
@login_required
def index():
    """Symptom screening questionnaire."""
    if current_user.role not in ['student', 'admin']:
        from flask import flash
        flash('Access denied.', 'error')
        return redirect(url_for('admin') if current_user.role == 'admin' else url_for('auth.login'))
    
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
    if current_user.role not in ['student', 'admin']:
        return redirect(url_for('admin') if current_user.role == 'admin' else url_for('auth.login'))
    
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


# ---------------------------------------------------------------------------
# Voice AI Triage — Gemini-powered voice symptom analysis
# ---------------------------------------------------------------------------
_voice_model = None

VOICE_TRIAGE_PROMPT = """You are a medical triage AI assistant for the ISUFST University Clinic. A student has described their symptoms via voice input.

Analyze the transcript and return a JSON response with EXACTLY this structure:
{
  "detected_symptoms": ["symptom1", "symptom2"],
  "recommended_service": "Medical",
  "severity": 3,
  "severity_label": "Routine",
  "suggestions": "Your analysis and advice here",
  "summary": "Brief one-line summary of the condition"
}

RULES:
- detected_symptoms: Extract specific symptoms from the transcript. Use standard medical symptom names.
- recommended_service: One of: "Medical", "Dental", "Mental Health", "Physical Therapy", "Laboratory", "Emergency"
- severity: 1 = Emergency (life-threatening), 2 = Urgent (needs prompt attention), 3 = Routine (can wait)
- severity_label: Must match severity number — "Emergency", "Urgent", or "Routine"
- suggestions: Provide helpful, empathetic advice. Mention they can book a FREE appointment at ISUFST Clinic through CareHub. Do NOT diagnose — use hedging language. For serious symptoms, urge immediately seeking help.
- summary: One concise sentence describing their likely issue.

IMPORTANT: Return ONLY valid JSON. No markdown, no code fences, no extra text."""


def _get_voice_model():
    global _voice_model
    if _voice_model is None:
        import google.generativeai as genai
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise RuntimeError('GEMINI_API_KEY environment variable is not set.')
        genai.configure(api_key=api_key)
        model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
        _voice_model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=VOICE_TRIAGE_PROMPT,
            generation_config={
                'temperature': 0.3,
                'max_output_tokens': 1024,
            },
        )
    return _voice_model


@symptom_screening.route('/voice-analyze', methods=['POST'])
@login_required
def voice_analyze():
    """Analyze voice transcript using Gemini AI for intelligent triage."""
    data = request.get_json()
    transcript = (data.get('transcript') or '').strip()

    if not transcript:
        return jsonify({'error': 'No voice transcript provided'}), 400

    if len(transcript) > 3000:
        return jsonify({'error': 'Transcript too long (max 3000 characters)'}), 400

    try:
        model = _get_voice_model()
        response = model.generate_content(f"Patient voice transcript: \"{transcript}\"")
        result_text = response.text.strip()

        # Clean potential markdown fences
        if result_text.startswith('```'):
            result_text = result_text.split('\n', 1)[1] if '\n' in result_text else result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()

        ai_result = json.loads(result_text)

        # Save screening record
        symptoms_list = ai_result.get('detected_symptoms', [])
        screening = SymptomScreening(
            student_id=current_user.id,
            symptoms_json=json.dumps(symptoms_list),
            severity_level=ai_result.get('severity', 3),
            recommended_service=ai_result.get('recommended_service', 'Medical'),
            ai_suggestions=ai_result.get('suggestions', '')
        )
        db.session.add(screening)
        db.session.commit()

        ai_result['screening_id'] = screening.id
        ai_result['should_book'] = ai_result.get('severity', 3) > 1
        return jsonify(ai_result)

    except json.JSONDecodeError:
        return jsonify({
            'detected_symptoms': [],
            'recommended_service': 'Medical',
            'severity': 3,
            'severity_label': 'Routine',
            'suggestions': 'I understood your symptoms but had trouble processing them. Please try the manual symptom checker or visit the clinic directly.',
            'summary': 'Unable to parse AI response',
            'should_book': True
        })
    except Exception as e:
        print(f'[Voice Triage Error] {e}')
        return jsonify({
            'error': 'AI analysis temporarily unavailable. Please use the manual symptom checker.'
        }), 500
