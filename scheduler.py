"""
Scheduled Tasks for ISUFST CareHub.
Automated jobs for reminders, expiry alerts, and maintenance.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, User, Appointment, Inventory
from models_extended import AppointmentExtended
from notification_service import notify_appointment_reminder, notify_expiring_medicines
from datetime import datetime, date, timedelta
from flask import current_app


scheduler = BackgroundScheduler()


def send_appointment_reminders():
    """Send reminders 24 hours before appointments."""
    with current_app.app_context():
        tomorrow = date.today() + timedelta(days=1)
        
        # Get appointments for tomorrow
        appointments = Appointment.query.filter(
            Appointment.appointment_date == tomorrow,
            Appointment.status.in_(['Confirmed', 'Pending'])
        ).all()
        
        for appt in appointments:
            # Check if reminder already sent
            ext = AppointmentExtended.query.filter_by(appointment_id=appt.id).first()
            if ext and not ext.reminder_sent:
                notify_appointment_reminder(appt, appt.student)
                ext.reminder_sent = True
        
        db.session.commit()
        print(f'[SCHEDULER] Sent {len(appointments)} appointment reminders')


def check_expiring_medicines():
    """Weekly check for expiring medicines and alert admins."""
    with current_app.app_context():
        # Get medicines expiring in next 30 days
        expiry_threshold = date.today() + timedelta(days=30)
        
        expiring = Inventory.query.filter(
            Inventory.category == 'Medicine',
            Inventory.expiry_date <= expiry_threshold,
            Inventory.expiry_date >= date.today(),
            Inventory.quantity > 0
        ).all()
        
        if expiring:
            # Get all admins
            admins = User.query.filter(
                User.role.in_(['admin', 'nurse']),
                User.is_active == True
            ).all()
            
            notify_expiring_medicines(admins, expiring)
            print(f'[SCHEDULER] Alerted {len(admins)} admins about {len(expiring)} expiring medicines')


def auto_cancel_no_shows():
    """Automatically mark missed appointments as no-show."""
    with current_app.app_context():
        yesterday = date.today() - timedelta(days=1)
        
        # Find appointments that were not completed/cancelled
        no_shows = Appointment.query.filter(
            Appointment.appointment_date < date.today(),
            Appointment.status.in_(['Pending', 'Confirmed'])
        ).all()
        
        count = 0
        for appt in no_shows:
            appt.status = 'No Show'
            count += 1
        
        db.session.commit()
        print(f'[SCHEDULER] Marked {count} appointments as no-show')


def cleanup_expired_inventory_locks():
    """Remove expired inventory locks."""
    with current_app.app_context():
        from models_extended import InventoryLock
        
        expired = InventoryLock.query.filter(
            InventoryLock.expires_at < datetime.now()
        ).all()
        
        for lock in expired:
            db.session.delete(lock)
        
        db.session.commit()
        print(f'[SCHEDULER] Cleaned up {len(expired)} expired inventory locks')


def expire_old_waitlist_entries():
    """Remove waitlist entries for past dates."""
    with current_app.app_context():
        from models_extended import AppointmentWaitlist
        
        expired = AppointmentWaitlist.query.filter(
            AppointmentWaitlist.preferred_date < date.today(),
            AppointmentWaitlist.status == 'Waiting'
        ).all()
        
        for entry in expired:
            entry.status = 'Expired'
        
        db.session.commit()
        print(f'[SCHEDULER] Expired {len(expired)} old waitlist entries')


def init_scheduler(app):
    """Initialize and start the scheduler."""
    # Daily reminder check at 9:00 AM
    scheduler.add_job(
        func=send_appointment_reminders,
        trigger='cron',
        hour=9,
        minute=0,
        id='appointment_reminders',
        replace_existing=True
    )
    
    # Weekly medicine expiry check (Monday 8:00 AM)
    scheduler.add_job(
        func=check_expiring_medicines,
        trigger='cron',
        day_of_week='mon',
        hour=8,
        minute=0,
        id='expiry_check',
        replace_existing=True
    )
    
    # Daily no-show check at midnight
    scheduler.add_job(
        func=auto_cancel_no_shows,
        trigger='cron',
        hour=0,
        minute=15,
        id='no_show_check',
        replace_existing=True
    )
    
    # Hourly cleanup of expired locks
    scheduler.add_job(
        func=cleanup_expired_inventory_locks,
        trigger='interval',
        hours=1,
        id='lock_cleanup',
        replace_existing=True
    )
    
    # Daily waitlist cleanup
    scheduler.add_job(
        func=expire_old_waitlist_entries,
        trigger='cron',
        hour=1,
        minute=0,
        id='waitlist_cleanup',
        replace_existing=True
    )
    
    scheduler.start()
    print('[SCHEDULER] Background scheduler started')
    
    # Ensure scheduler stops on app shutdown
    import atexit
    atexit.register(lambda: scheduler.shutdown())
