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
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.utils import ImageReader
import os
import io
import base64
import qrcode

certificates = Blueprint('certificates', __name__, url_prefix='/certificates')


def require_staff(f):
    """Decorator to require nurse or admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['admin']:
            flash('Access denied. Staff only.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@certificates.route('/admin')
@login_required
@require_staff
def admin_certificates():
    """Admin page to manage certificates."""
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
        
        if not student_id or not purpose:
            flash('Student and purpose are required.', 'error')
            return redirect(url_for('certificates.issue_certificate'))
        
        student = User.query.get(student_id)
        if not student or student.role != 'student':
            flash('Invalid student selected.', 'error')
            return redirect(url_for('certificates.issue_certificate'))
        
        last_cert = HealthCertificate.query.order_by(HealthCertificate.id.desc()).first()
        cert_number = f"HC-{date.today().year}-{(last_cert.id + 1) if last_cert else 1:04d}"
        
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
        
        from notification_service import notify_certificate_issued
        notify_certificate_issued(student, certificate)
        
        flash(f'Certificate {cert_number} issued successfully to {student.full_name}!', 'success')
        return redirect(url_for('certificates.admin_certificates'))
    
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
    
    if current_user.role == 'student' and cert.student_id != current_user.id:
        flash('You can only view your own certificates.', 'error')
        return redirect(url_for('patient_dashboard.index'))
    
    return render_template('view_certificate.html', certificate=cert)


@certificates.route('/verify/<string:cert_number>')
def verify_certificate(cert_number):
    """Public verification page for certificates (accessible via QR code)."""
    cert = HealthCertificate.query.filter_by(certificate_number=cert_number).first()
    
    if not cert:
        return render_template('verify_certificate.html', valid=False, cert_number=cert_number)
    
    student = cert.student
    profile = student.student_profile
    
    return render_template(
        'verify_certificate.html',
        valid=True,
        certificate=cert,
        student=student,
        profile=profile
    )


@certificates.route('/download/<int:cert_id>')
@login_required
def download_certificate(cert_id):
    """Generate and download PDF certificate - Professional 2026 Design."""
    cert = HealthCertificate.query.get_or_404(cert_id)
    
    if current_user.role == 'student' and cert.student_id != current_user.id:
        flash('You can only download your own certificates.', 'error')
        return redirect(url_for('patient_dashboard.index'))
    
    # Generate PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=1.3*inch,
        bottomMargin=1.2*inch,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # ========== COLOR PALETTE ==========
    PRIMARY_BLUE = colors.HexColor('#1e3a5f')
    SECONDARY_BLUE = colors.HexColor('#2563eb')
    ACCENT_BLUE = colors.HexColor('#3b82f6')
    TEXT_DARK = colors.HexColor('#1e293b')
    TEXT_GRAY = colors.HexColor('#64748b')
    TEXT_LIGHT = colors.HexColor('#94a3b8')
    
    # ========== STYLES ==========
    university_style = ParagraphStyle(
        'UniversityName',
        parent=styles['Normal'],
        fontSize=10,
        textColor=PRIMARY_BLUE,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=12
    )
    
    certificate_title_style = ParagraphStyle(
        'CertificateTitle',
        parent=styles['Normal'],
        fontSize=22,
        textColor=PRIMARY_BLUE,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontSize=10,
        textColor=TEXT_DARK,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        spaceAfter=4,
        spaceBefore=8
    )
    
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        textColor=TEXT_GRAY,
        fontName='Helvetica-Bold'
    )
    
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=10,
        textColor=TEXT_DARK,
        fontName='Helvetica'
    )
    
    # ========== LOAD LOGOS ==========
    def load_logo(path, width, height):
        if os.path.exists(path):
            try:
                return Image(path, width=width, height=height)
            except:
                return None
        return None
    
    # Header Logos
    isufst_logo = load_logo(os.path.join('static', 'images', 'isufst-logo.png'), 1*inch, 0.7*inch)
    bayan_logo = load_logo(os.path.join('static', 'images', 'bayan.png'), 0.6*inch, 0.6*inch)
    
    # Footer Logos (Increased size)
    heart_logo = load_logo(os.path.join('static', 'images', 'heart.png'), 0.6*inch, 0.6*inch)
    gcl_logo = load_logo(os.path.join('static', 'images', 'gcl.png'), 0.6*inch, 0.6*inch)
    
    def draw_fixed_elements(canvas, doc):
        canvas.saveState()
        
        # --- HEADER ---
        header_data = [
            [isufst_logo or '', Paragraph("<b>ILOILO STATE UNIVERSITY OF<br/>FISHERIES SCIENCE AND TECHNOLOGY</b>", university_style), bayan_logo or '']
        ]
        header_table = Table(header_data, colWidths=[1.2*inch, 5.1*inch, 1.2*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ]))
        
        # Wrap and draw header at the absolute top margin
        header_table.wrapOn(canvas, doc.width, doc.topMargin)
        header_table.drawOn(canvas, doc.leftMargin, doc.height + doc.bottomMargin + 0.3*inch)
        
        # Separator line
        canvas.setStrokeColor(PRIMARY_BLUE)
        canvas.setLineWidth(1)
        line_y = doc.height + doc.bottomMargin + 0.2*inch
        canvas.line(doc.leftMargin, line_y, doc.leftMargin + doc.width, line_y)
        
        # --- FOOTER ---
        core_values = Paragraph(
            "<b>INTEGRITY</b>  •  <b>SOCIAL JUSTICE</b>  •  <b>DISCIPLINE</b>  •  <b>ACADEMIC EXCELLENCE</b>",
            ParagraphStyle('CoreValues', parent=styles['Normal'], fontSize=8, textColor=TEXT_DARK, alignment=TA_CENTER, fontName='Helvetica-Bold')
        )
        
        logos_row = []
        if heart_logo: logos_row.append(heart_logo)
        if gcl_logo: logos_row.append(gcl_logo)
        
        if logos_row:
            logos_table = Table([logos_row], colWidths=[0.65*inch]*len(logos_row))
            logos_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            footer_table = Table([[core_values, logos_table]], colWidths=[6.0*inch, 1.5*inch])
            footer_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ]))
        else:
            footer_table = Table([[core_values]], colWidths=[7.5*inch])
            footer_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'CENTER'), ('VALIGN', (0, 0), (0, 0), 'MIDDLE')]))
            
        footer_table.wrapOn(canvas, doc.width, doc.bottomMargin)
        footer_table.drawOn(canvas, doc.leftMargin, 0.6*inch)
        
        contact_info = Paragraph(
            "For verification: clinic@isufst.edu.ph | www.isufst.edu.ph",
            ParagraphStyle('ContactInfo', parent=styles['Normal'], fontSize=7, textColor=TEXT_GRAY, alignment=TA_CENTER)
        )
        contact_info.wrapOn(canvas, doc.width, doc.bottomMargin)
        contact_info.drawOn(canvas, doc.leftMargin, 0.4*inch)
        
        verify_text = Paragraph(
            "<i>This certificate is digitally signed and cryptographically verified. Tampering invalidates this document.</i>",
            ParagraphStyle('VerifyText', parent=styles['Normal'], fontSize=6, textColor=TEXT_LIGHT, alignment=TA_CENTER)
        )
        verify_text.wrapOn(canvas, doc.width, doc.bottomMargin)
        verify_text.drawOn(canvas, doc.leftMargin, 0.25*inch)
        
        canvas.restoreState()
    
    # Certificate title (First flowable element)
    title_para = Paragraph(
        "<font color='#1e3a5f'><b>OFFICIAL HEALTH CERTIFICATE</b></font>",
        certificate_title_style
    )
    elements.append(title_para)
    elements.append(Spacer(1, 0.1*inch))
    
    # ========== CERTIFICATE INFO BAR ==========
    student = cert.student
    profile = student.student_profile
    
    cert_info_data = [
        [
            Paragraph("<font color='#64748b'>Certificate No:</font>", label_style),
            Paragraph(f"<b>{cert.certificate_number}</b>", value_style),
            Paragraph("<font color='#64748b'>Date Issued:</font>", label_style),
            Paragraph(cert.issued_at.strftime('%B %d, %Y'), value_style)
        ],
        [
            Paragraph("<font color='#64748b'>Valid Until:</font>", label_style),
            Paragraph(cert.valid_until.strftime('%B %d, %Y') if cert.valid_until else 'N/A', value_style),
            Paragraph("<font color='#64748b'>Status:</font>", label_style),
            Paragraph("<font color='#059669'><b>VALID</b></font>", value_style)
        ]
    ]
    
    cert_info_table = Table(cert_info_data, colWidths=[1.2*inch, 1.8*inch, 1.2*inch, 1.8*inch])
    cert_info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(cert_info_table)
    elements.append(Spacer(1, 0.1*inch))
    
    # ========== SALUTATION ==========
    salutation = Paragraph(
        "<b>TO WHOM IT MAY CONCERN:</b>",
        ParagraphStyle(
            'Salutation',
            parent=styles['Normal'],
            fontSize=11,
            textColor=TEXT_DARK,
            spaceAfter=8
        )
    )
    elements.append(salutation)
    
    certifying_text = Paragraph(
        "This is to certify that the individual named below has been examined at the Iloilo State University of Fisheries Science and Technology Health Services and has been found to be in the specified medical condition.",
        ParagraphStyle(
            'CertifyingText',
            parent=styles['Normal'],
            fontSize=10,
            textColor=TEXT_GRAY,
            leading=14,
            spaceAfter=12
        )
    )
    elements.append(certifying_text)
    
    # ========== STUDENT INFORMATION BOX ==========
    student_name = student.full_name
    student_id_num = profile.student_id_number if profile else 'N/A'
    course_year = 'N/A'
    if profile and profile.course:
        suffix = ['st', 'nd', 'rd', 'th'][min(profile.year_level - 1, 3) if profile.year_level and profile.year_level > 0 else 3]
        course_year = f"{profile.course} - {profile.year_level}{suffix} Year"
    
    # Student info with bordered box
    student_info_data = [
        [Paragraph("<b>NAME:</b>", label_style), Paragraph(student_name, value_style)],
        [Paragraph("<b>STUDENT ID:</b>", label_style), Paragraph(student_id_num, value_style)],
        [Paragraph("<b>COURSE & YEAR:</b>", label_style), Paragraph(course_year, value_style)],
        [Paragraph("<b>BLOOD TYPE:</b>", label_style), Paragraph(profile.blood_type if profile and profile.blood_type else 'Not recorded', value_style)]
    ]
    
    student_table = Table(student_info_data, colWidths=[1.8*inch, 4.8*inch])
    student_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BORDER', (0, 0), (-1, -1), 0.5),
        ('LINEABOVE', (0, 0), (-1, 0), 1, PRIMARY_BLUE),
        ('LINEBELOW', (0, -1), (-1, -1), 1, PRIMARY_BLUE),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(student_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # ========== MEDICAL FINDINGS ==========
    elements.append(Paragraph("MEDICAL FINDINGS", section_heading_style))
    findings_text = cert.medical_findings or "General health check completed. No significant medical findings."
    findings_para = Paragraph(
        findings_text,
        ParagraphStyle(
            'Findings',
            parent=styles['Normal'],
            fontSize=10,
            textColor=TEXT_DARK,
            leading=14,
            spaceAfter=8
        )
    )
    elements.append(findings_para)
    
    # ========== PURPOSE ==========
    elements.append(Paragraph("PURPOSE OF CERTIFICATE", section_heading_style))
    purpose_para = Paragraph(
        cert.purpose or "General purpose",
        ParagraphStyle(
            'Purpose',
            parent=styles['Normal'],
            fontSize=10,
            textColor=TEXT_DARK,
            leading=14
        )
    )
    elements.append(purpose_para)
    elements.append(Spacer(1, 0.2*inch))
    
    # ========== DIGITAL SIGNATURE SECTION ==========
    issuer = cert.issuer
    
    # Generate QR code for verification
    verification_url = f"https://isufst-clinic.onrender.com/certificates/verify/{cert.certificate_number}"
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(verification_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR to buffer
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_image = Image(qr_buffer, width=0.8*inch, height=0.8*inch)
    
    # Signature section
    sig_layout = []
    
    # Digital signature badge
    signature_badge = Table([['DIGITALLY SIGNED']], colWidths=[2*inch])
    signature_badge.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#dbeafe')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1e40af')),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 8),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('PADDING', (0, 0), (0, 0), 3),
    ]))
    
    # Signature image or line
    if issuer.signature_data and issuer.signature_data.startswith('data:image'):
        try:
            sig_base64 = issuer.signature_data.split(',')[1]
            sig_bytes = base64.b64decode(sig_base64)
            sig_image = Image(io.BytesIO(sig_bytes), width=2*inch, height=0.7*inch)
            sig_content = sig_image
        except:
            sig_content = Paragraph("<font color='#94a3b8'>[Signature Image]</font>", value_style)
    else:
        sig_content = Paragraph("<font color='#94a3b8'>___________________________</font>", value_style)
    
    qr_text_style = ParagraphStyle(
        'QRText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=TEXT_GRAY,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=10
    )
    
    # Group QR code and its text
    qr_cell = Table([
        [qr_image],
        [Paragraph("Scan to verify<br/>online authenticity", qr_text_style)]
    ], colWidths=[2*inch])
    qr_cell.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 1), (-1, 1), 2), # Small padding above text
    ]))
    
    # Signature details
    issuer_name = issuer.full_name
    issuer_role = "Clinic Nurse" if issuer.role == 'nurse' else "Health Services"
    
    # Group signature content
    sig_text_cell = Table([
        [Paragraph(f"<b>{issuer_name}</b>", value_style)],
        [Paragraph(f"{issuer_role}<br/><font color='#64748b'>Iloilo State University of Fisheries Science and Technology</font>", label_style)]
    ], colWidths=[4*inch])
    sig_text_cell.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    
    sig_details = [
        [sig_content, qr_cell],
        [sig_text_cell, '']
    ]
    
    sig_table = Table(sig_details, colWidths=[4*inch, 2*inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (1, 0), (1, 1)), # Span the right column across both rows
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    
    elements.append(sig_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Verification note
    verify_note = Paragraph(
        f"<font color='#64748b'><i>Document ID: {cert.certificate_number} | Signed: {cert.issued_at.strftime('%B %d, %Y at %I:%M %p')} | This certificate is digitally signed and cryptographically verified.</i></font>",
        ParagraphStyle(
            'VerifyNote',
            parent=styles['Normal'],
            fontSize=7,
            textColor=TEXT_GRAY,
            alignment=TA_CENTER,
            spaceAfter=6
        )
    )
    elements.append(verify_note)
    
    # Build PDF with fixed header/footer layout
    doc.build(elements, onFirstPage=draw_fixed_elements, onLaterPages=draw_fixed_elements)
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
