import os
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

from config import config
from models import db

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
        app.config['SQLALCHEMY_DATABASE_URI'] = config[config_name].SQLALCHEMY_DATABASE_URI

    # -- Init extensions --------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    CORS(app)

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
    app.register_blueprint(auth)
    app.register_blueprint(appointments)
    app.register_blueprint(queue)
    app.register_blueprint(inventory)
    app.register_blueprint(reservations)

    # -- Routes -----------------------------------
    @app.route('/')
    def index():
        """Student client homepage"""
        from flask import render_template
        return render_template('index.html')

    @app.route('/admin')
    def admin():
        """Admin dashboard with real data"""
        from flask import render_template
        from models import Queue, Inventory, Appointment, ClinicVisit
        from utils import get_next_patient
        from datetime import date

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

        return render_template(
            'admin.html',
            next_patient=next_patient,
            queue_count=queue_count,
            today_patients=today_patients,
            today_appointments=today_appointments,
            expiring_items=expiring_items[:5],
            low_stock_count=low_stock_count
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

    # -- Create tables (dev convenience) ----------
    with app.app_context():
        db.create_all()

    return app


# -- Entry point ----------------------------------
if __name__ == '__main__':
    application = create_app()
    application.run(debug=True, port=5000)
