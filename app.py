import os
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, CSRFError

from config import config
from models import db
from rbac import init_rbac

# -- Extension instances --------------------------
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name=None):
    """Application factory for ISUFST CareHub."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__, static_folder='static', template_folder='templates')

    # -- Load config ------------------------------
    app.config.from_object(config[config_name])
    if hasattr(config[config_name], 'init_app'):
        config[config_name].init_app()
    
    # Always re-evaluate database URI to ensure env vars are loaded
    from config import Config
    app.config['SQLALCHEMY_DATABASE_URI'] = Config._get_database_uri()

    # -- Init extensions --------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configure CSRF to accept headers from AJAX requests
    app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # Disable CSRF token expiration
    
    csrf.init_app(app)
    CORS(app)
    init_rbac(app)  # Initialize RBAC system

    # Ensure extended models are registered for migrations
    import models_extended  # noqa: F401

    # Handle CSRF errors gracefully for JSON API requests
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        from flask import request as req, jsonify as jfy
        if req.is_json or req.headers.get('Content-Type', '').startswith('application/json'):
            return jfy({'error': 'CSRF token missing. Please refresh the page and try again.'}), 400
        from flask import flash, redirect, url_for
        flash('Session expired. Please try again.', 'error')
        return redirect(req.referrer or url_for('index'))

    # -- Flask-Login config -----------------------
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # -- Register blueprints ----------------------
    from auth import auth
    from appointments import appointments
    from clinic_queue import queue
    from inventory import inventory
    from reservations import reservations
    from notifications import notifications
    from logbook import logbook
    from patient_dashboard import patient_dashboard
    from analytics import analytics
    from api import api_v1
    from queue_display import queue_display, socketio as queue_socketio
    from search import search
    from symptom_screening import symptom_screening
    from chatbot import chatbot
    from certificates import certificates
    
    app.register_blueprint(auth)
    app.register_blueprint(appointments)
    app.register_blueprint(queue)
    app.register_blueprint(inventory)
    app.register_blueprint(reservations)
    app.register_blueprint(notifications)
    app.register_blueprint(logbook)
    app.register_blueprint(patient_dashboard)
    app.register_blueprint(analytics)
    app.register_blueprint(api_v1)
    app.register_blueprint(queue_display)
    app.register_blueprint(search)
    app.register_blueprint(symptom_screening)
    app.register_blueprint(chatbot)
    app.register_blueprint(certificates)
    
    # Initialize SocketIO
    queue_socketio.init_app(app, cors_allowed_origins="*")
    
    # Initialize notification service
    from notification_service import init_notification_service
    init_notification_service(app)
    
    # Initialize scheduler
    from scheduler import init_scheduler
    init_scheduler(app)

    # -- Routes -----------------------------------
    @app.route('/')
    def index():
        """Student client homepage with dynamic slot data."""
        from flask import render_template
        from models import Appointment
        from datetime import date, datetime, timedelta
        
        # Get today's available slots (PH timezone = UTC+8)
        from zoneinfo import ZoneInfo
        ph_tz = ZoneInfo('Asia/Manila')
        ph_now = datetime.now(ph_tz)
        today = ph_now.date()
        current_hour = ph_now.hour
        current_minute = ph_now.minute
        
        # Generate time slots for today
        clinic_start = 9
        clinic_end = 17
        slot_duration = 30
        
        slots = []
        current = datetime.strptime(f'{clinic_start}:00', '%H:%M')
        end = datetime.strptime(f'{clinic_end}:00', '%H:%M')
        
        while current < end:
            slot_hour = current.hour
            slot_minute = current.minute
            
            # Check if slot is in the past (PH time)
            is_past = (slot_hour < current_hour) or (slot_hour == current_hour and slot_minute <= current_minute)
            
            # Count existing appointments for this slot
            slot_time = current.strftime('%H:%M')
            booked = Appointment.query.filter(
                Appointment.appointment_date == today,
                Appointment.start_time == datetime.strptime(slot_time, '%H:%M').time(),
                Appointment.status.in_(['Pending', 'Confirmed'])
            ).count()
            
            slots.append({
                'time': current.strftime('%I:%M %p'),
                'is_past': is_past,
                'is_booked': booked >= 3,  # Max 3 per slot
                'available': not is_past and booked < 3
            })
            current += timedelta(minutes=slot_duration)
        
        available_count = sum(1 for s in slots if s['available'])
        
        return render_template('index.html',
                             today_slots=slots[:8],
                             available_count=available_count,
                             ph_time=ph_now.strftime('%I:%M %p'))

    @app.route('/admin')
    @login_required
    def admin():
        """Admin dashboard with real data"""
        from flask import render_template, abort
        from models import Queue, Inventory, Appointment, ClinicVisit, MedicineReservation, User
        from utils import get_next_patient
        from datetime import date

        if current_user.role not in ['admin', 'nurse']:
            abort(403)

        next_patient = get_next_patient()
        queue_count = Queue.query.filter_by(status='Waiting').count()
        today_patients = ClinicVisit.query.filter(
            ClinicVisit.visit_date == date.today()
        ).count()
        today_appointments = Appointment.query.filter(
            Appointment.appointment_date == date.today()
        ).count()

        expiring_items = []
        all_items = Inventory.query.filter(
            Inventory.category == 'Medicine',
            Inventory.quantity > 0
        ).order_by(Inventory.expiry_date.asc()).limit(10).all()
        for item in all_items:
            if item.is_expiring_soon():
                expiring_items.append(item)

        low_stock_count = Inventory.query.filter(
            Inventory.quantity < 10
        ).count()

        # Appointments for today
        todays_appts = Appointment.query.filter(
            Appointment.appointment_date == date.today()
        ).order_by(Appointment.start_time.asc()).all()

        # Pending reservations
        pending_reservations = MedicineReservation.query.filter_by(
            status='Reserved'
        ).order_by(MedicineReservation.reserved_at.desc()).limit(10).all()

        # Total students
        total_students = User.query.filter_by(role='student').count()

        return render_template(
            'admin.html',
            next_patient=next_patient,
            queue_count=queue_count,
            today_patients=today_patients,
            today_appointments=today_appointments,
            expiring_items=expiring_items[:5],
            low_stock_count=low_stock_count,
            todays_appts=todays_appts,
            pending_reservations=pending_reservations,
            total_students=total_students
        )

    @app.route('/health')
    def health():
        return {'status': 'ok', 'app': 'ISUFST CareHub'}, 200

    # -- Seed demo admin account ------------------
    @app.cli.command('seed-admin')
    def seed_admin():
        """Create a demo admin account."""
        from models import User
        admin = User.query.filter_by(email='admin@isufst.edu.ph').first()
        if not admin:
            admin = User(
                email='admin@isufst.edu.ph',
                first_name='Admin',
                last_name='CareHub',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Demo admin created: admin@isufst.edu.ph / admin123')
        else:
            print('Admin account already exists.')

    # -- Create tables & seed admin ----------
    with app.app_context():
        try:
            print("📋 Creating database tables (if they don't exist)...")
            db.create_all()
            print("✅ Database tables ready")
            
            # Auto-seed admin account
            from models import User
            admin = User.query.filter_by(email='admin@isufst.edu.ph').first()
            if not admin:
                admin = User(
                    email='admin@isufst.edu.ph',
                    first_name='Admin',
                    last_name='CareHub',
                    role='admin'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print('🔑 Admin account created: admin@isufst.edu.ph / admin123')
            else:
                print('✅ Admin account already exists')
        except Exception as e:
            print(f"⚠️  Database initialization warning: {str(e)}")
            import traceback
            traceback.print_exc()

    return app


# -- Entry point ----------------------------------
if __name__ == '__main__':
    application = create_app()
    application.run(debug=True, port=5000)
