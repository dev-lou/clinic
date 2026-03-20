import os
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_compress import Compress
from flask_caching import Cache

from config import config
from models import db
from rbac import init_rbac

# -- Extension instances --------------------------
migrate  = Migrate()
login_manager = LoginManager()
csrf     = CSRFProtect()
compress = Compress()
cache    = Cache()


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
    from config import get_database_uri
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()

    # -- Init extensions --------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configure CSRF to accept headers from AJAX requests
    app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # Disable CSRF token expiration
    
    csrf.init_app(app)
    CORS(app)

    # Gzip/Brotli response compression (60-80% payload savings)
    app.config['COMPRESS_REGISTER'] = True
    app.config['COMPRESS_LEVEL']    = 6   # balanced speed/ratio
    compress.init_app(app)

    # In-memory short-lived cache (no Redis needed)
    app.config['CACHE_TYPE']             = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT']  = 60
    cache.init_app(app)

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

    @app.errorhandler(404)
    def not_found_error(e):
        from flask import render_template as rt
        return rt('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        from flask import render_template as rt
        return rt('errors/500.html'), 500

    # -- Flask-Login config -----------------------
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        # db.session.get() uses SQLAlchemy's identity map — avoids redundant
        # DB round-trip if the User object is already in the current session.
        return db.session.get(User, int(user_id))

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
        from sqlalchemy import func
        
        # Get today's available slots (PH timezone = UTC+8)
        from zoneinfo import ZoneInfo
        ph_tz = ZoneInfo('Asia/Manila')
        ph_now = datetime.now(ph_tz)
        today = ph_now.date()
        current_hour = ph_now.hour
        current_minute = ph_now.minute
        
        # --- PERF: Single batch query instead of N queries in a loop ---
        # Fetch all booked slot counts for today in one grouped query
        from sqlalchemy import func
        booked_rows = db.session.query(
            Appointment.start_time,
            func.count(Appointment.id).label('cnt')
        ).filter(
            Appointment.appointment_date == today,
            Appointment.status.in_(['Pending', 'Confirmed'])
        ).group_by(Appointment.start_time).all()
        # Build a fast lookup dict:  time_obj -> count
        booked_counts = {row.start_time: row.cnt for row in booked_rows}
        
        clinic_start   = 9
        clinic_end     = 17
        slot_duration  = 30
        
        slots: list[dict] = []
        current = datetime.strptime(f'{clinic_start}:00', '%H:%M')
        end     = datetime.strptime(f'{clinic_end}:00',   '%H:%M')
        
        while current < end:
            slot_hour   = current.hour
            slot_minute = current.minute
            is_past     = (slot_hour < current_hour) or (
                           slot_hour == current_hour and slot_minute <= current_minute)
            
            slot_time_obj = current.time()
            booked        = booked_counts.get(slot_time_obj, 0)
            
            slots.append({
                'time':      current.strftime('%I:%M %p'),
                'is_past':   is_past,
                'is_booked': booked >= 3,
                'available': not is_past and booked < 3
            })
            current += timedelta(minutes=slot_duration)
        
        available_count: int = sum(1 for s in slots if s['available'])
        
        return render_template('index.html',
                             today_slots=slots,
                             available_count=available_count,
                             ph_time=ph_now.strftime('%I:%M %p'))

    @app.route('/admin')
    @login_required
    def admin():
        """Admin dashboard with real data — stats cached for 30 s."""
        from flask import render_template, abort
        from models import Queue, Inventory, Appointment, ClinicVisit, MedicineReservation, User
        from utils import get_next_patient
        from datetime import date

        if current_user.role != 'admin':
            abort(403)

        cache_key = f'admin_dashboard_{date.today()}'
        cached = cache.get(cache_key)
        if cached:
            return render_template('admin.html', **cached)

        next_patient = get_next_patient()
        queue_count  = Queue.query.filter_by(status='Waiting').count()
        today        = date.today()

        today_patients     = ClinicVisit.query.filter(ClinicVisit.visit_date == today).count()
        today_appointments = Appointment.query.filter(Appointment.appointment_date == today).count()
        low_stock_count    = Inventory.query.filter(Inventory.quantity < 10).count()
        total_students     = User.query.filter_by(role='student').count()

        expiring_items: list[Inventory] = [
            item for item in Inventory.query.filter(
                Inventory.category == 'Medicine',
                Inventory.quantity > 0
            ).order_by(Inventory.expiry_date.asc()).limit(10).all()
            if item.is_expiring_soon()
        ]

        todays_appts = Appointment.query.filter(
            Appointment.appointment_date == today
        ).order_by(Appointment.start_time.asc()).all()

        pending_reservations = MedicineReservation.query.filter_by(
            status='Reserved'
        ).order_by(MedicineReservation.reserved_at.desc()).limit(10).all()

        ctx = dict(
            next_patient=next_patient,
            queue_count=queue_count,
            today_patients=today_patients,
            today_appointments=today_appointments,
            expiring_items=expiring_items[:5],
            low_stock_count=low_stock_count,
            todays_appts=todays_appts,
            pending_reservations=pending_reservations,
            total_students=total_students,
        )
        cache.set(cache_key, ctx, timeout=30)   # cache for 30 seconds
        return render_template('admin.html', **ctx)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'app': 'ISUFST CareHub'}, 200

    # -- Seed demo admin account ------------------


    # -- Create tables & seed admin ----------
    return app


# -- Entry point ----------------------------------
if __name__ == '__main__':
    application = create_app()
    application.run(debug=True, port=5000)
