"""
AI Chatbot Blueprint — ISUFST CareHub
Uses Google Gemini to provide symptom/health Q&A for students.
"""

import os
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user

chatbot = Blueprint('chatbot', __name__, url_prefix='/chatbot')

# ---------------------------------------------------------------------------
# Gemini client (lazy-loaded)
# ---------------------------------------------------------------------------
_model = None


def _get_model():
    """Lazy-load the Gemini generative model."""
    global _model
    if _model is None:
        import google.generativeai as genai

        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise RuntimeError('GEMINI_API_KEY environment variable is not set.')

        genai.configure(api_key=api_key)

        model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
        _model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
            generation_config={
                'temperature': 0.7,
                'max_output_tokens': 1024,
            },
        )
        print(f'[Chatbot] Gemini model loaded: {model_name}')
    return _model


# ---------------------------------------------------------------------------
# System prompt — constrains the chatbot to health / clinic topics
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are CareHub AI, a friendly and helpful health assistant for the ISUFST University Clinic (Iloilo Science and Technology University - Fischer Town campus).

ROLE & SCOPE:
- Answer health-related questions: common symptoms, first-aid tips, general wellness advice, medicine information.
- Help students decide whether they should visit the clinic.
- Provide general information about common illnesses, treatments, and preventive care.
- You may suggest over-the-counter remedies for minor ailments (headache, colds, minor cuts).
- Keep your language warm, approachable, and easy to understand.

IMPORTANT RULES:
1. You are NOT a licensed doctor. Include a brief disclaimer when you give medical advice or when symptoms could be concerning. Do not repeat it in every single message.
2. For serious symptoms (chest pain, difficulty breathing, severe bleeding, allergic reactions, etc.), immediately advise the student to seek emergency help or visit the clinic RIGHT AWAY.
3. Always encourage students to book a FREE check-up at the ISUFST Clinic through CareHub when appropriate.
4. Do NOT diagnose conditions. Use phrases like "this might be", "it could be", "it's possible that".
5. Do NOT prescribe prescription medications. You may mention common OTC options.
6. If the question is NOT related to health, wellness, the clinic, or CareHub services, politely redirect: "I'm focused on health and clinic topics. For other questions, please contact the ISUFST administration."
7. Keep responses concise (2-4 paragraphs max).
8. Use bullet points or numbered lists when listing symptoms or steps.
9. When relevant, mention that the ISUFST Clinic offers free consultations, basic medicines, and health services to students.

EXAMPLE DISCLAIMERS (use only when needed, vary them naturally):
- "Remember, I'm an AI assistant — not a doctor. If symptoms persist, please visit the clinic for a proper check-up! 🏥"
- "This is general advice only. For a professional opinion, book a free appointment at the ISUFST Clinic through CareHub."

ABOUT CAREHUB:
- CareHub is the ISUFST Clinic's digital platform for booking appointments, reserving medicines, and tracking health records.
- Students can book appointments for Medical Consultation, Dental Check-up, Physical Exam, First Aid, and more.
- The clinic provides FREE services to all enrolled ISUFST students.
"""


# ---------------------------------------------------------------------------
# Chat API
# ---------------------------------------------------------------------------
@chatbot.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """Process a chat message via Gemini and return the response."""
    data = request.get_json(force=True, silent=True) or {}
    user_message = (data.get('message') or '').strip()

    if not user_message:
        return jsonify({'error': 'Message is required.'}), 400

    if len(user_message) > 2000:
        return jsonify({'error': 'Message is too long (max 2000 characters).'}), 400

    try:
        model = _get_model()

        response = model.generate_content(user_message)

        assistant_text = response.text

        return jsonify({'reply': assistant_text})

    except Exception as e:
        print(f'[Chatbot Error] {e}')
        return jsonify({
            'reply': "I'm sorry, I'm having trouble connecting right now. Please try again in a moment, or visit the ISUFST Clinic directly for assistance. 🏥"
        })
