"""
Health Certificate Management for ISUFST CareHub.
Handles certificate issuance, viewing, and PDF generation.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from models import db, User, ClinicVisit, StudentProfile
from models_extended import HealthCertificate
from datetime import datetime, timezone, date, timedelta
from functools import wraps
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.utils import ImageReader
import os
import io
import base64

certificates = Blueprint('certificates', __name__, url_prefix='/certificates')


def require_staff(f):
    """Decorator to require nurse or admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['nurse', 'admin']:
            flash('Access denied. Staff only.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@certificates.route('/admin')
@login_required
@require_staff
def admin_certificates():
    """Admin page to manage certificates."""
    # Get all issued certificates
    certs = HealthCertificate.query.order_by(HealthCertificate.issued_at.desc()).all()
    return render_template('admin_certificates.html', certificates=certs, today=date.today())


@certificates.route('/admin/issue', methods=['GET', 'POST'])
@login_required
@require_staff
def issue_certificate():
    """Issue a new health certificate."""
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        visit_id = request.form.get('visit_id', type=int)
        purpose = request.form.get('purpose')
        medical_findings = request.form.get('medical_findings')
        valid_months = request.form.get('valid_months', type=int, default=3)
        
        # Validate
        if not student_id or not purpose:
            flash('Student and purpose are required.', 'error')
            return redirect(url_for('certificates.issue_certificate'))
        
        student = User.query.get(student_id)
        if not student or student.role != 'student':
            flash('Invalid student selected.', 'error')
            return redirect(url_for('certificates.issue_certificate'))
        
        # Generate certificate number
        last_cert = HealthCertificate.query.order_by(HealthCertificate.id.desc()).first()
        cert_number = f"HC-{date.today().year}-{(last_cert.id + 1) if last_cert else 1:04d}"
        
        # Create certificate
        certificate = HealthCertificate(
            student_id=student_id,
            issued_by=current_user.id,
            certificate_number=cert_number,
            purpose=purpose,
            medical_findings=medical_findings or 'General health check completed. No significant findings.',
            valid_until=date.today() + timedelta(days=valid_months * 30)
        )
        
        db.session.add(certificate)
        db.session.commit()
        
        flash(f'Certificate {cert_number} issued successfully to {student.full_name}!', 'success')
        return redirect(url_for('certificates.admin_certificates'))
    
    # GET - show form
    # Get students with completed visits in last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_visits = ClinicVisit.query.filter(
        ClinicVisit.status == 'completed',
        ClinicVisit.visit_date >= thirty_days_ago
    ).order_by(ClinicVisit.visit_date.desc()).all()
    
    return render_template('issue_certificate.html', recent_visits=recent_visits)


@certificates.route('/api/search-students')
@login_required
@require_staff
def search_students_api():
    """API: Search students by name or ID for certificate issuance."""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    # Search by name or student ID
    students = User.query.join(StudentProfile).filter(
        User.role == 'student',
        db.or_(
            User.first_name.ilike(f'%{query}%'),
            User.last_name.ilike(f'%{query}%'),
            StudentProfile.student_id_number.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    results = []
    for student in students:
        profile = student.student_profile
        # Get latest completed visit
        latest_visit = ClinicVisit.query.filter_by(
            student_id=student.id,
            status='completed'
        ).order_by(ClinicVisit.visit_date.desc()).first()
        
        results.append({
            'id': student.id,
            'name': student.full_name,
            'student_id': profile.student_id_number if profile else 'N/A',
            'course': profile.course if profile else 'N/A',
            'year_level': profile.year_level if profile else None,
            'latest_visit': {
                'id': latest_visit.id,
                'date': latest_visit.visit_date.strftime('%b %d, %Y'),
                'diagnosis': latest_visit.diagnosis or 'No diagnosis recorded',
                'treatment': latest_visit.treatment or 'No treatment recorded'
            } if latest_visit else None
        })
    
    return jsonify(results)


@certificates.route('/view/<int:cert_id>')
@login_required
def view_certificate(cert_id):
    """View certificate details (student can only view their own)."""
    cert = HealthCertificate.query.get_or_404(cert_id)
    
    # Check permissions
    if current_user.role == 'student' and cert.student_id != current_user.id:
        flash('You can only view your own certificates.', 'error')
        return redirect(url_for('patient_dashboard.index'))
    
    return render_template('view_certificate.html', certificate=cert)


@certificates.route('/download/<int:cert_id>')
@login_required
def download_certificate(cert_id):
    """Generate and download PDF certificate."""
    cert = HealthCertificate.query.get_or_404(cert_id)
    
    # Check permissions
    if current_user.role == 'student' and cert.student_id != current_user.id:
        flash('You can only download your own certificates.', 'error')
        return redirect(url_for('patient_dashboard.index'))
    
    # Generate PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Professional Header with Logos
    header_elements = []
    
    # ISUFST Logo (left)
    isufst_logo_path = os.path.join('static', 'images', 'isufst-logo.png')
    isufst_logo = None
    if os.path.exists(isufst_logo_path):
        try:
            isufst_logo = Image(isufst_logo_path, width=1.2*inch, height=0.8*inch)
        except:
            isufst_logo = ''
    else:
        isufst_logo = ''
    
    # Center Text
    header_text = Paragraph(
        "<b>ILOILO STATE UNIVERSITY OF FISHERIES SCIENCE AND TECHNOLOGY</b><br/>"
        "<font size=10>CareHub</font><br/>"
        "<font size=9>HEALTH CERTIFICATE</font>",
        ParagraphStyle(
            'HeaderCenter',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1e293b'),
            leading=14
        )
    )
    
    # Bagong Pilipinas Logo (right)
    bayan_logo_path = os.path.join('static', 'images', 'bayan.png')
    bayan_logo = None
    if os.path.exists(bayan_logo_path):
        try:
            bayan_logo = Image(bayan_logo_path, width=0.8*inch, height=0.8*inch)
        except:
            bayan_logo = ''
    else:
        bayan_logo = ''
    
    # Create header table
    header_data = [[isufst_logo, header_text, bayan_logo]]
    header_table = Table(header_data, colWidths=[1.2*inch, 5*inch, 1.2*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Certificate details table
    student = cert.student
    profile = student.student_profile
    
    cert_info = [
        ['Certificate No:', cert.certificate_number, 'Date Issued:', cert.issued_at.strftime('%B %d, %Y')],
        ['Valid Until:', cert.valid_until.strftime('%B %d, %Y') if cert.valid_until else 'N/A', '', ''],
    ]
    
    cert_table = Table(cert_info, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    cert_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#64748b')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(cert_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Student Information
    elements.append(Paragraph("STUDENT INFORMATION", heading_style))
    student_info = [
        ['Name:', student.full_name],
        ['Student ID:', profile.student_id_number if profile else 'N/A'],
        ['Course & Year:', f"{profile.course} - {profile.year_level}{['st','nd','rd','th'][min(profile.year_level-1,3) if profile.year_level else 3]} Year" if profile and profile.course else 'N/A'],
        ['Blood Type:', profile.blood_type if profile and profile.blood_type else 'Not on record'],
    ]
    
    student_table = Table(student_info, colWidths=[1.5*inch, 5*inch])
    student_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(student_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Medical Findings
    elements.append(Paragraph("MEDICAL FINDINGS", heading_style))
    findings_text = cert.medical_findings or "General health check completed. No significant medical findings."
    elements.append(Paragraph(findings_text, styles['Normal']))
    elements.append(Spacer(1, 0.15*inch))
    
    # Purpose
    elements.append(Paragraph("PURPOSE", heading_style))
    elements.append(Paragraph(cert.purpose or "General purpose", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Signature Section
    issuer = cert.issuer
    
    # If issuer has a digital signature, use it
    if issuer.signature_data and issuer.signature_data.startswith('data:image'):
        try:
            # Extract base64 data
            sig_base64 = issuer.signature_data.split(',')[1]
            sig_bytes = base64.b64decode(sig_base64)
            sig_image = Image(io.BytesIO(sig_bytes), width=2*inch, height=0.8*inch)
            
            sig_data = [
                ['', ''],
                [sig_image, ''],
                [f"{issuer.full_name}, RN", ''],
                ['Issued by:', ''],
                ['ISUFST Dingle Campus Health Services', ''],
            ]
        except:
            # Fallback if signature parsing fails
            sig_data = [
                ['', ''],
                ['_'*40, ''],
                [f"{issuer.full_name}, RN", ''],
                ['Issued by:', ''],
                ['ISUFST Dingle Campus Health Services', ''],
            ]
    else:
        # No signature - use line
        sig_data = [
            ['', ''],
            ['_'*40, ''],
            [f"{issuer.full_name}, RN", ''],
            ['Issued by:', ''],
            ['ISUFST Dingle Campus Health Services', ''],
        ]
    
    sig_table = Table(sig_data, colWidths=[3*inch, 3*inch])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 3), (0, 3), colors.HexColor('#64748b')),
        ('FONTSIZE', (0, 3), (0, 4), 8),
    ]))
    elements.append(sig_table)
    
    # Footer with Core Values and Accreditation Logo
    elements.append(Spacer(1, 0.3*inch))
    
    # Core values text
    core_values_text = Paragraph(
        "<b>Integrity</b> . <b>Social Justice</b> . <b>Discipline</b> . <b>Academic Excellence</b>",
        ParagraphStyle(
            'CoreValues',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#1e293b'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
    )
    
    # Accreditation logos (GCL and Heart)
    gcl_logo_path = os.path.join('static', 'images', 'gcl.png')
    heart_logo_path = os.path.join('static', 'images', 'heart.png')
    
    gcl_logo = None
    if os.path.exists(gcl_logo_path):
        try:
            gcl_logo = Image(gcl_logo_path, width=1.2*inch, height=0.8*inch)
        except:
            gcl_logo = ''
    else:
        gcl_logo = ''
    
    heart_logo = None
    if os.path.exists(heart_logo_path):
        try:
            heart_logo = Image(heart_logo_path, width=1.2*inch, height=0.8*inch)
        except:
            heart_logo = ''
    else:
        heart_logo = ''
    
    # Combine logos in a nested table
    if gcl_logo and heart_logo:
        logos_table = Table([[gcl_logo, heart_logo]], colWidths=[1.3*inch, 1.3*inch])
        logos_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        logos_cell = logos_table
    elif gcl_logo:
        logos_cell = gcl_logo
    elif heart_logo:
        logos_cell = heart_logo
    else:
        logos_cell = ''
    
    # Create footer table
    footer_data = [[core_values_text, logos_cell]]
    footer_table = Table(footer_data, colWidths=[4*inch, 2.5*inch])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(footer_table)
    
    # Additional footer info
    elements.append(Spacer(1, 0.1*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#94a3b8'),
        alignment=TA_CENTER
    )
    elements.append(Paragraph(
        "This is an official health certificate issued by Iloilo State University of Fisheries Science and Technology Health Services.<br/>"
        "For verification, please contact the clinic at clinic@isufst.edu.ph",
        footer_style
    ))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Health_Certificate_{cert.certificate_number}.pdf'
    )


@certificates.route('/admin/<int:cert_id>/delete', methods=['POST'])
@login_required
@require_staff
def delete_certificate(cert_id):
    """Delete a certificate (admin only)."""
    if current_user.role != 'admin':
        flash('Only admins can delete certificates.', 'error')
        return redirect(url_for('certificates.admin_certificates'))
    
    cert = HealthCertificate.query.get_or_404(cert_id)
    cert_number = cert.certificate_number
    
    db.session.delete(cert)
    db.session.commit()
    
    flash(f'Certificate {cert_number} deleted successfully.', 'success')
    return redirect(url_for('certificates.admin_certificates'))
