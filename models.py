from datetime import datetime, timezone, date, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


# ──────────────────────────────────────────────
#  User / Auth
# ──────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    role = db.Column(
        db.String(20),
        nullable=False,
        default='student',  # student | nurse | admin
    )
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    student_profile = db.relationship(
        'StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan'
    )
    clinic_visits = db.relationship(
        'ClinicVisit', backref='patient', lazy='dynamic', foreign_keys='ClinicVisit.student_id'
    )

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def set_password(self, password):
        """Hash and store password using bcrypt."""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against stored hash."""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


# ──────────────────────────────────────────────
#  Student Profile
# ──────────────────────────────────────────────
class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    student_id_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    course = db.Column(db.String(120))
    year_level = db.Column(db.Integer)
    contact_number = db.Column(db.String(20))
    emergency_contact_name = db.Column(db.String(128))
    emergency_contact_number = db.Column(db.String(20))
    blood_type = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    medical_conditions = db.Column(db.Text)

    def __repr__(self):
        return f'<StudentProfile {self.student_id_number}>'


# ──────────────────────────────────────────────
#  Clinic Visits
# ──────────────────────────────────────────────
class ClinicVisit(db.Model):
    __tablename__ = 'clinic_visits'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    attending_nurse_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    visit_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    chief_complaint = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.Text)
    treatment = db.Column(db.Text)
    notes = db.Column(db.Text)
    status = db.Column(
        db.String(20),
        default='pending',  # pending | in_progress | completed
    )

    # Relationships
    attending_nurse = db.relationship('User', foreign_keys=[attending_nurse_id])
    medications_given = db.relationship(
        'MedicationLog', backref='visit', lazy='dynamic', cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<ClinicVisit #{self.id} – {self.status}>'


# ──────────────────────────────────────────────
#  Medication Inventory
# ──────────────────────────────────────────────
class Medication(db.Model):
    __tablename__ = 'medications'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text)
    quantity_in_stock = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(30), default='pcs')  # pcs | tablets | ml | etc.
    expiry_date = db.Column(db.Date)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f'<Medication {self.name} (qty: {self.quantity_in_stock})>'


# ──────────────────────────────────────────────
#  Medication Log  (dispensed per visit)
# ──────────────────────────────────────────────
class MedicationLog(db.Model):
    __tablename__ = 'medication_logs'

    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('clinic_visits.id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.id'), nullable=False)
    quantity_given = db.Column(db.Integer, nullable=False, default=1)
    remarks = db.Column(db.Text)
    dispensed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    medication = db.relationship('Medication')

    def __repr__(self):
        return f'<MedicationLog visit={self.visit_id} med={self.medication_id}>'


# ──────────────────────────────────────────────
#  Inventory (FIFO Logic)
# ──────────────────────────────────────────────
class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    batch_number = db.Column(db.String(64), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(
        db.String(20),
        nullable=False,
        default='Medicine'  # Medicine | Equipment
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def is_expiring_soon(self):
        """Returns True if the expiry date is within 30 days."""
        if not self.expiry_date:
            return False
        today = date.today()
        days_until_expiry = (self.expiry_date - today).days
        return 0 <= days_until_expiry <= 30

    def __repr__(self):
        return f'<Inventory {self.name} batch={self.batch_number} qty={self.quantity}>'


# ──────────────────────────────────────────────
#  Appointment (Conflict Logic)
# ──────────────────────────────────────────────
class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    service_type = db.Column(
        db.String(20),
        nullable=False,
        default='Medical'  # Dental | Medical
    )
    appointment_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(
        db.String(20),
        nullable=False,
        default='Pending'  # Pending | Confirmed | Completed | Cancelled
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    student = db.relationship('User', backref='appointments')

    def has_conflict(self, other_appointment):
        """Check if this appointment conflicts with another appointment."""
        if self.appointment_date != other_appointment.appointment_date:
            return False
        if self.service_type != other_appointment.service_type:
            return False
        # Check time overlap
        return (
            (self.start_time < other_appointment.end_time) and
            (self.end_time > other_appointment.start_time)
        )

    def __repr__(self):
        return f'<Appointment #{self.id} {self.service_type} on {self.appointment_date} – {self.status}>'


# ──────────────────────────────────────────────
#  Queue (Priority Logic)
# ──────────────────────────────────────────────
class Queue(db.Model):
    __tablename__ = 'queues'

    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(128), nullable=False)
    severity_score = db.Column(
        db.Integer,
        nullable=False,
        default=3  # 1=Emergency, 2=Urgent, 3=Routine
    )
    arrival_time = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default='Waiting'  # Waiting | Serving
    )

    @property
    def priority_label(self):
        """Returns a human-readable priority label."""
        labels = {1: 'Emergency', 2: 'Urgent', 3: 'Routine'}
        return labels.get(self.severity_score, 'Unknown')

    def __repr__(self):
        return f'<Queue #{self.id} {self.student_name} – {self.priority_label} – {self.status}>'


# 
#  Medicine Reservation
# -
class MedicineReservation(db.Model):
    __tablename__ = 'medicine_reservations'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    medicine_name = db.Column(db.String(128), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    status = db.Column(db.String(20), default='Reserved', nullable=False)
    reserved_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    picked_up_at = db.Column(db.DateTime(timezone=True))
    notes = db.Column(db.Text)

    student = db.relationship('User', backref='medicine_reservations')

    def __repr__(self):
        return f'<MedicineReservation {self.medicine_name} - {self.student_id}>'
