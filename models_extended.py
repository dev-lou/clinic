"""
Extended models for ISUFST CareHub - Business Logic Enhancements.
These models enhance the existing system with proper relationships and workflows.
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


class PrescriptionStatus(Enum):
    """Prescription lifecycle states."""
    PENDING = 'Pending'
    DISPENSED = 'Dispensed'
    PARTIALLY_DISPENSED = 'Partially Dispensed'
    CANCELLED = 'Cancelled'


# ──────────────────────────────────────────────
#  Doctor Schedule Management
# ──────────────────────────────────────────────
class DoctorSchedule(db.Model):
    """Weekly schedule template for doctors/staff."""
    __tablename__ = 'doctor_schedules'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    service_type = db.Column(db.String(50), nullable=False)  # Medical, Dental, etc.
    max_patients = db.Column(db.Integer, default=5)  # Max patients per slot
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    doctor = db.relationship('User', backref='schedules', foreign_keys=[doctor_id])

    __table_args__ = (
        CheckConstraint('day_of_week >= 0 AND day_of_week <= 6', name='valid_day_of_week'),
        UniqueConstraint('doctor_id', 'day_of_week', 'start_time', 'service_type', name='unique_doctor_schedule'),
    )

    def __repr__(self):
        return f'<DoctorSchedule Dr {self.doctor_id} Day {self.day_of_week}>'


class DoctorLeave(db.Model):
    """Track doctor absences and holidays."""
    __tablename__ = 'doctor_leaves'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    leave_date = db.Column(db.Date, nullable=False, index=True)
    reason = db.Column(db.String(200))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    doctor = db.relationship('User', backref='leaves', foreign_keys=[doctor_id])

    __table_args__ = (
        UniqueConstraint('doctor_id', 'leave_date', name='unique_doctor_leave'),
    )

    def __repr__(self):
        return f'<DoctorLeave Dr {self.doctor_id} on {self.leave_date}>'


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
#  Appointment Waitlist
# ──────────────────────────────────────────────
class AppointmentWaitlist(db.Model):
    """Waitlist for fully booked appointment slots."""
    __tablename__ = 'appointment_waitlist'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    service_type = db.Column(db.String(50), nullable=False)
    preferred_date = db.Column(db.Date, nullable=False, index=True)
    preferred_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Waiting', nullable=False)  # Waiting, Notified, Converted, Expired
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    notified_at = db.Column(db.DateTime(timezone=True))
    converted_to_appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))

    # Relationships
    student = db.relationship('User', backref='waitlist_entries', foreign_keys=[student_id])
    converted_appointment = db.relationship('Appointment')

    def __repr__(self):
        return f'<Waitlist student={self.student_id} date={self.preferred_date}>'


# ──────────────────────────────────────────────
#  Prescription & Dispensing Workflow
# ──────────────────────────────────────────────
class Prescription(db.Model):
    """Proper prescription tracking linked to visits."""
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('clinic_visits.id'), nullable=False, index=True)
    prescribed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    status = db.Column(db.String(30), default='Pending', nullable=False)
    prescribed_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    digital_signature = db.Column(db.Text)  # Encrypted doctor signature
    notes = db.Column(db.Text)

    # Relationships
    visit = db.relationship('ClinicVisit', backref='prescriptions')
    doctor = db.relationship('User', foreign_keys=[prescribed_by], backref='prescriptions_written')
    patient = db.relationship('User', foreign_keys=[patient_id])
    items = db.relationship('PrescriptionItem', backref='prescription', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Prescription #{self.id} visit={self.visit_id}>'


class PrescriptionItem(db.Model):
    """Individual medicines in a prescription."""
    __tablename__ = 'prescription_items'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    quantity_prescribed = db.Column(db.Integer, nullable=False)
    quantity_dispensed = db.Column(db.Integer, default=0, nullable=False)
    dosage_instructions = db.Column(db.Text)
    dispensed_at = db.Column(db.DateTime(timezone=True))
    dispensed_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relationships
    medicine = db.relationship('Inventory')
    dispenser = db.relationship('User', foreign_keys=[dispensed_by])

    def __repr__(self):
        return f'<PrescriptionItem rx={self.prescription_id} med={self.inventory_id}>'


# ──────────────────────────────────────────────
#  Inventory Reservation Lock (Atomic Operations)
# ──────────────────────────────────────────────
class InventoryLock(db.Model):
    """Lock inventory during reservation to prevent race conditions."""
    __tablename__ = 'inventory_locks'

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False, index=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('medicine_reservations.id'), nullable=False)
    quantity_locked = db.Column(db.Integer, nullable=False)
    locked_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)  # Auto-release after 24h

    # Relationships
    inventory = db.relationship('Inventory', backref='locks')
    reservation = db.relationship('MedicineReservation', backref='inventory_lock')

    def __repr__(self):
        return f'<InventoryLock inv={self.inventory_id} qty={self.quantity_locked}>'


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
#  Audit Logging System
# ──────────────────────────────────────────────
class AuditLog(db.Model):
    """Comprehensive audit trail for compliance."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)  # login, create, update, delete, access
    resource_type = db.Column(db.String(50), nullable=False)  # User, Appointment, Visit, etc.
    resource_id = db.Column(db.Integer, nullable=True)
    old_value = db.Column(db.Text)  # JSON of old state
    new_value = db.Column(db.Text)  # JSON of new state
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action} on {self.resource_type}#{self.resource_id}>'


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
