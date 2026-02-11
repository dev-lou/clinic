"""
Utility functions for advanced features.
QR code generation, PDF certificates, symptom screening logic.
"""
import qrcode
from io import BytesIO
import base64
from datetime import datetime, date, timedelta
import json
import secrets


# ──────────────────────────────────────────────
#  QR Code Generation
# ──────────────────────────────────────────────

def generate_qr_code(data, size=10, add_logo=False):
    """
    Generate QR code for appointment check-in.
    Returns base64-encoded image string.
    
    Args:
        data: QR code data string
        size: Box size for QR code
        add_logo: If True, adds favicon logo in center
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction for logo overlay
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Add logo in center if requested
    if add_logo:
        try:
            from PIL import Image, ImageDraw
            import os
            
            # Get favicon path
            logo_path = os.path.join(os.path.dirname(__file__), 'static', 'favicon.ico')
            
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                
                # Calculate logo size (12% of QR code - smaller for better scanner compatibility)
                qr_width, qr_height = img.size
                logo_size = int(qr_width * 0.12)
                padding = 4  # White padding around logo
                
                # Resize logo (handle different Pillow versions)
                try:
                    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                except AttributeError:
                    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
                
                # Convert logo to RGB if needed (in case it's RGBA)
                if logo.mode != 'RGB':
                    logo_bg = Image.new('RGB', (logo_size, logo_size), 'white')
                    if logo.mode == 'RGBA':
                        logo_bg.paste(logo, (0, 0), logo)
                    else:
                        logo = logo.convert('RGB')
                        logo_bg = logo
                    logo = logo_bg
                
                # Create white background box (slightly larger than logo for padding)
                bg_size = logo_size + padding * 2
                logo_bg_box = Image.new('RGB', (bg_size, bg_size), 'white')
                logo_bg_box.paste(logo, (padding, padding))
                
                # Calculate position (center)
                logo_pos = ((qr_width - bg_size) // 2, (qr_height - bg_size) // 2)
                
                # Paste logo with white background
                img.paste(logo_bg_box, logo_pos)
        except Exception as e:
            # If logo fails, continue without it
            print(f"Warning: Could not add logo to QR code: {e}")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    
    return f'data:image/png;base64,{img_base64}'


def generate_appointment_qr(appointment_id):
    """Generate QR code for appointment check-in with ISUFST logo."""
    # Create secure token
    token = secrets.token_urlsafe(32)
    
    # QR data includes appointment ID and token (30 days expiration for consistency)
    qr_data = json.dumps({
        'type': 'appointment_checkin',
        'appointment_id': appointment_id,
        'token': token,
        'expires': (datetime.now() + timedelta(days=30)).isoformat()
    })
    
    qr_image = generate_qr_code(qr_data, add_logo=True)  # Add branded logo
    
    return qr_image, token


def generate_reservation_qr(reservation_id):
    """Generate QR code for medicine reservation check-in."""
    token = secrets.token_urlsafe(32)

    qr_data = json.dumps({
        'type': 'medicine_reservation',
        'reservation_id': reservation_id,
        'token': token,
        'expires': (datetime.now() + timedelta(days=30)).isoformat()
    })

    qr_image = generate_qr_code(qr_data, add_logo=True)

    return qr_image, token


def verify_qr_checkin(qr_data_json):
    """Verify QR code for check-in."""
    try:
        data = json.loads(qr_data_json)
        
        # Check expiration
        expires = datetime.fromisoformat(data['expires'])
        if datetime.now() > expires:
            return False, 'QR code expired'
        
        # Verify appointment exists
        from models import Appointment
        appt = Appointment.query.get(data['appointment_id'])
        if not appt:
            return False, 'Invalid appointment'
        
        # Verify token matches
        from models_extended import AppointmentExtended
        ext = AppointmentExtended.query.filter_by(appointment_id=data['appointment_id']).first()
        if not ext or ext.qr_code != data['token']:
            return False, 'Invalid QR code'
        
        return True, appt
    except Exception as e:
        return False, str(e)


# ──────────────────────────────────────────────
#  Symptom Pre-Screening Logic
# ──────────────────────────────────────────────

SYMPTOM_RULES = {
    # Emergency symptoms
    'emergency': [
        'chest pain', 'difficulty breathing', 'severe bleeding',
        'unconscious', 'seizure', 'severe head injury', 'poisoning'
    ],
    
    # Dental symptoms
    'dental': [
        'toothache', 'tooth pain', 'gum bleeding', 'wisdom tooth',
        'dental cavity', 'broken tooth', 'jaw pain'
    ],
    
    # Mental health indicators
    'mental_health': [
        'anxiety', 'depression', 'stress', 'panic attack',
        'insomnia', 'suicidal thoughts', 'emotional distress'
    ],
    
    # Physical therapy indicators
    'physical_therapy': [
        'sprain', 'muscle pain', 'joint pain', 'back pain',
        'sports injury', 'rehabilitation'
    ],
    
    # Laboratory test needed
    'laboratory': [
        'blood test', 'urinalysis', 'pregnancy test', 'drug test',
        'check up', 'medical clearance'
    ]
}


def analyze_symptoms(symptoms_text):
    """
    Analyze symptoms and recommend service type.
    Returns (service_type, severity_level, suggestions).
    """
    symptoms_lower = symptoms_text.lower()
    
    # Check for emergency
    for symptom in SYMPTOM_RULES['emergency']:
        if symptom in symptoms_lower:
            return 'Emergency', 1, 'Please go to the nearest hospital emergency room immediately.'
    
    # Check specific services
    if any(symptom in symptoms_lower for symptom in SYMPTOM_RULES['dental']):
        return 'Dental', 3, 'Your symptoms suggest you may need dental care.'
    
    if any(symptom in symptoms_lower for symptom in SYMPTOM_RULES['mental_health']):
        return 'Mental Health', 2, 'Consider booking a mental health counseling appointment.'
    
    if any(symptom in symptoms_lower for symptom in SYMPTOM_RULES['physical_therapy']):
        return 'Physical Therapy', 3, 'Your symptoms may benefit from physical therapy.'
    
    if any(symptom in symptoms_lower for symptom in SYMPTOM_RULES['laboratory']):
        return 'Laboratory', 3, 'You may need laboratory tests. Book a medical appointment.'
    
    # Default to medical
    return 'Medical', 3, 'Please book a general medical consultation.'


def calculate_severity_score(symptoms_list):
    """Calculate severity score based on symptom combinations."""
    score = 3  # Default: routine
    
    symptoms_text = ' '.join(symptoms_list).lower()
    
    # Emergency indicators
    if any(symptom in symptoms_text for symptom in SYMPTOM_RULES['emergency']):
        score = 1
    
    # Urgent indicators
    elif 'severe' in symptoms_text or 'intense' in symptoms_text or 'unbearable' in symptoms_text:
        score = 2
    
    # High fever
    elif 'high fever' in symptoms_text or '39' in symptoms_text or '40' in symptoms_text:
        score = 2
    
    return score


# ──────────────────────────────────────────────
#  Health Certificate PDF Generation
# ──────────────────────────────────────────────

def generate_health_certificate_pdf(certificate):
    """
    Generate PDF for health certificate.
    Uses ReportLab for PDF generation.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        
        # Create PDF buffer
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2, height - inch, "Iloilo State University of Fisheries")
        c.drawCentredString(width / 2, height - 1.4*inch, "Science and Technology")
        
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width / 2, height - 2*inch, "HEALTH CERTIFICATE")
        
        # Certificate number
        c.setFont("Helvetica", 10)
        c.drawRightString(width - inch, height - 2.5*inch, f"Certificate No: {certificate.certificate_number}")
        
        # Body
        y_position = height - 3*inch
        c.setFont("Helvetica", 12)
        
        c.drawString(inch, y_position, f"This is to certify that:")
        y_position -= 0.5*inch
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1.5*inch, y_position, f"{certificate.student.first_name} {certificate.student.last_name}")
        y_position -= 0.4*inch
        
        c.setFont("Helvetica", 12)
        if certificate.student.student_profile:
            c.drawString(1.5*inch, y_position, f"Student ID: {certificate.student.student_profile.student_id_number}")
            y_position -= 0.3*inch
            c.drawString(1.5*inch, y_position, f"Course: {certificate.student.student_profile.course or 'N/A'}")
            y_position -= 0.5*inch
        
        c.drawString(inch, y_position, f"has been examined on {certificate.issued_at.strftime('%B %d, %Y')} and found to be:")
        y_position -= 0.4*inch
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1.5*inch, y_position, "PHYSICALLY FIT")
        y_position -= 0.5*inch
        
        c.setFont("Helvetica", 12)
        if certificate.medical_findings:
            c.drawString(inch, y_position, "Medical Findings:")
            y_position -= 0.3*inch
            c.drawString(1.5*inch, y_position, certificate.medical_findings[:100])
            y_position -= 0.5*inch
        
        c.drawString(inch, y_position, f"Purpose: {certificate.purpose or 'General'}")
        y_position -= 0.5*inch
        
        if certificate.valid_until:
            c.drawString(inch, y_position, f"Valid Until: {certificate.valid_until.strftime('%B %d, %Y')}")
            y_position -= inch
        
        # Signature
        y_position -= 0.5*inch
        c.drawString(4*inch, y_position, "_" * 30)
        y_position -= 0.3*inch
        c.drawString(4*inch, y_position, f"{certificate.issuer.first_name} {certificate.issuer.last_name}")
        y_position -= 0.2*inch
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(4*inch, y_position, "University Physician")
        
        # Footer
        c.setFont("Helvetica", 8)
        c.drawCentredString(width / 2, inch, "This is a computer-generated certificate.")
        
        c.save()
        
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        # If reportlab not installed, return None
        return None


def save_certificate_pdf(certificate, output_path):
    """Save certificate PDF to file."""
    pdf_data = generate_health_certificate_pdf(certificate)
    if pdf_data:
        with open(output_path, 'wb') as f:
            f.write(pdf_data)
        return output_path
    return None


# ──────────────────────────────────────────────
#  Audit Logging Helpers
# ──────────────────────────────────────────────

def log_audit(user_id, action, resource_type, resource_id, old_value=None, new_value=None, request_obj=None):
    """Create an audit log entry."""
    from models_extended import AuditLog
    from models import db
    import json as json_lib
    
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=json_lib.dumps(old_value) if old_value else None,
        new_value=json_lib.dumps(new_value) if new_value else None,
        ip_address=request_obj.remote_addr if request_obj else None,
        user_agent=request_obj.userAgent.string if request_obj and hasattr(request_obj, 'user_agent') else None
    )
    
    db.session.add(log)
    db.session.commit()
