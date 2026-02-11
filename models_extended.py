"""
Extended models for ISUFST CareHub - Essential Features Only.
Keeps only high-impact features: QR codes, feedback, certificates, symptom screening.
"""
from datetime import datetime, timezone, date, timedelta, time
from models import db
from sqlalchemy import CheckConstraint, UniqueConstraint
from enum import Enum


# ──────────────────────────────────────────────
#  Enums for Business Logic
# ──────────────────────────────────────────────
class AppointmentStatus(Enum):
    """Appointment lifecycle states."""
    PENDING = 'Pending'
    CONFIRMED = 'Confirmed'
    IN_PROGRESS = 'In Progress'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'
    NO_SHOW = 'No Show'
    RESCHEDULED = 'Rescheduled'


class ServiceType(Enum):
    """Available clinic services."""
    MEDICAL = 'Medical'
    DENTAL = 'Dental'
    MENTAL_HEALTH = 'Mental Health'
    PHYSICAL_THERAPY ='Physical Therapy'
    LABORATORY = 'Laboratory'
    MEDICAL_CERTIFICATE = 'Medical Certificate'
    VACCINATION = 'Vaccination'


# ──────────────────────────────────────────────
#  Enhanced Appointment with Doctor Assignment
# ──────────────────────────────────────────────
class AppointmentExtended(db.Model):
    """Extension to Appointment model with doctor/dentist assignment.
    
    Notes:
    - assigned_doctor_id: Points to doctor (consultation) or dentist (dental care)
    - Nurses are assistants only and are not assigned to appointments
    """
    __tablename__ = 'appointment_extensions'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), unique=True, nullable=False)
    assigned_doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # Doctor or Dentist
    queue_id = db.Column(db.Integer, db.ForeignKey('queues.id'), nullable=True)  # Link to queue
    qr_code = db.Column(db.String(200), unique=True)  # QR code for check-in
    confirmation_sent = db.Column(db.Boolean, default=False)
    reminder_sent = db.Column(db.Boolean, default=False)
    
    # State transition tracking
    previous_status = db.Column(db.String(20))
    status_changed_at = db.Column(db.DateTime(timezone=True))
    status_changed_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relationships
    appointment = db.relationship('Appointment', backref=db.backref('extension', uselist=False))
    assigned_doctor = db.relationship('User', foreign_keys=[assigned_doctor_id], backref='assigned_appointments')
    queue = db.relationship('Queue', backref='appointment_link')
    status_changer = db.relationship('User', foreign_keys=[status_changed_by])

    def __repr__(self):
        return f'<AppointmentExtended appt_id={self.appointment_id}>'


# ──────────────────────────────────────────────
#  Medicine Reservation QR Extension
# ──────────────────────────────────────────────
class MedicineReservationExtended(db.Model):
    """Extension for medicine reservation QR codes."""
    __tablename__ = 'medicine_reservation_extensions'

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('medicine_reservations.id'), unique=True, nullable=False)
    qr_code = db.Column(db.String(200), unique=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    reservation = db.relationship('MedicineReservation', backref=db.backref('extension', uselist=False))

    def __repr__(self):
        return f'<MedicineReservationExtended reservation_id={self.reservation_id}>'


# ──────────────────────────────────────────────
#  Feedback & Rating System
# ──────────────────────────────────────────────
class VisitFeedback(db.Model):
    """Patient feedback after completed visits."""
    __tablename__ = 'visit_feedback'

    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('clinic_visits.id'), unique=True, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    wait_time_rating = db.Column(db.Integer)  # 1-5
    staff_rating = db.Column(db.Integer)  # 1-5
    facility_rating = db.Column(db.Integer)  # 1-5
    comments = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    visit = db.relationship('ClinicVisit', backref=db.backref('feedback', uselist=False))
    student = db.relationship('User')

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='valid_rating'),
    )

    def __repr__(self):
        return f'<VisitFeedback visit={self.visit_id} rating={self.rating}>'


# ──────────────────────────────────────────────
#  Health Certificate Generation
# ──────────────────────────────────────────────
class HealthCertificate(db.Model):
    """Generated health certificates for students."""
    __tablename__ = 'health_certificates'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    issued_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    certificate_number = db.Column(db.String(50), unique=True, nullable=False)
    purpose = db.Column(db.String(200))  # School requirement, Employment, etc.
    medical_findings = db.Column(db.Text)
    issued_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    valid_until = db.Column(db.Date)
    pdf_path = db.Column(db.String(500))  # Path to generated PDF
    digital_signature = db.Column(db.Text)

    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='health_certificates')
    issuer = db.relationship('User', foreign_keys=[issued_by])

    def __repr__(self):
        return f'<HealthCertificate #{self.certificate_number}>'


# ──────────────────────────────────────────────
#  Symptom Pre-Screening
# ──────────────────────────────────────────────
class SymptomScreening(db.Model):
    """AI-powered symptom pre-screening responses."""
    __tablename__ = 'symptom_screenings'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    symptoms_json = db.Column(db.Text, nullable=False)  # JSON array of symptoms
    severity_level = db.Column(db.Integer, default=3)  # 1=Emergency, 5=Routine
    recommended_service = db.Column(db.String(50))  # Medical, Dental, Mental Health, etc.
    ai_suggestions = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    linked_appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))

    # Relationships
    student = db.relationship('User', backref='symptom_screenings')
    appointment = db.relationship('Appointment')

    def __repr__(self):
        return f'<SymptomScreening student={self.student_id} severity={self.severity_level}>'
