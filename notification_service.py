"""
Notification Service for ISUFST CareHub.
Handles email, SMS, and in-app notifications.
"""
import os
import requests
from datetime import datetime, timezone
from flask import current_app
from flask_mail import Mail, Message as EmailMessage
from models import db, Notification


# Initialize Flask-Mail (configured in app.py)
mail = Mail()


def create_notification(user_id, type, title, message, link=None):
    """Create an in-app notification."""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        link=link
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def send_email(to_email, subject, body_html, body_text=None):
    """Send email notification using Flask-Mail."""
    try:
        msg = EmailMessage(
            subject=subject,
            recipients=[to_email],
            html=body_html,
            body=body_text or body_html
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Email send failed: {str(e)}")
        return False


def send_sms(phone_number, message):
    """
    Send SMS via Semaphore API (Philippine SMS provider).
    
    Configure in .env:
        SEMAPHORE_API_KEY=your_api_key
    """
    api_key = os.environ.get('SEMAPHORE_API_KEY')
    if not api_key:
        current_app.logger.warning("SEMAPHORE_API_KEY not configured")
        return False
    
    # Format phone number (should be 63XXXXXXXXXX for PH)
    if phone_number.startswith('0'):
        phone_number = '63' + phone_number[1:]
    
    try:
        response = requests.post(
            'https://api.semaphore.co/api/v4/messages',
            data={
                'apikey': api_key,
                'number': phone_number,
                'message': message,
                'sendername': 'ISUFST'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return True
        else:
            current_app.logger.error(f"SMS send failed: {response.text}")
            return False
    except Exception as e:
        current_app.logger.error(f"SMS exception: {str(e)}")
        return False


# ──────────────────────────────────────────────
#  Appointment Notifications
# ──────────────────────────────────────────────

def notify_appointment_confirmation(appointment, user):
    """Send appointment confirmation via email, SMS, and in-app."""
    from datetime import datetime
    
    # In-app notification
    create_notification(
        user_id=user.id,
        type='appointment_confirmed',
        title='Appointment Confirmed',
        message=f'Your {appointment.service_type} appointment on {appointment.appointment_date.strftime("%B %d, %Y")} at {appointment.start_time.strftime("%I:%M %p")} has been confirmed.',
        link=f'/appointments/my'
    )
    
    # Email
    email_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Appointment Confirmed</h2>
            <p>Dear {user.first_name},</p>
            <p>Your appointment has been confirmed:</p>
            <ul>
                <li><strong>Service:</strong> {appointment.service_type}</li>
                <li><strong>Date:</strong> {appointment.appointment_date.strftime("%B %d, %Y")}</li>
                <li><strong>Time:</strong> {appointment.start_time.strftime("%I:%M %p")}</li>
            </ul>
            <p>Please arrive 10 minutes early. Bring your student ID.</p>
            <p><strong>ISUFST CareHub</strong></p>
        </body>
    </html>
    """
    send_email(user.email, 'Appointment Confirmed - ISUFST CareHub', email_body)
    
    # SMS
    if hasattr(user, 'student_profile') and user.student_profile and user.student_profile.contact_number:
        sms_message = f"ISUFST CareHub: Your {appointment.service_type} appointment on {appointment.appointment_date.strftime('%m/%d/%Y')} at {appointment.start_time.strftime('%I:%M %p')} is confirmed. See you!"
        send_sms(user.student_profile.contact_number, sms_message)


def notify_appointment_reminder(appointment, user):
    """Send appointment reminder 24 hours before."""
    create_notification(
        user_id=user.id,
        type='appointment_reminder',
        title='Appointment Reminder',
        message=f'Reminder: You have a {appointment.service_type} appointment tomorrow at {appointment.start_time.strftime("%I:%M %p")}.',
        link=f'/appointments/my'
    )
    
    # Email reminder
    email_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Appointment Reminder</h2>
            <p>Dear {user.first_name},</p>
            <p>This is a reminder of your upcoming appointment:</p>
            <ul>
                <li><strong>Service:</strong> {appointment.service_type}</li>
                <li><strong>Date:</strong> {appointment.appointment_date.strftime("%B %d, %Y")}</li>
                <li><strong>Time:</strong> {appointment.start_time.strftime("%I:%M %p")}</li>
            </ul>
            <p>Please arrive 10 minutes early.</p>
            <p><strong>ISUFST CareHub</strong></p>
        </body>
    </html>
    """
    send_email(user.email, 'Appointment Reminder - Tomorrow', email_body)
    
    # SMS reminder
    if hasattr(user, 'student_profile') and user.student_profile and user.student_profile.contact_number:
        sms_message = f"ISUFST: Reminder - You have a {appointment.service_type} appointment tomorrow at {appointment.start_time.strftime('%I:%M %p')}. See you!"
        send_sms(user.student_profile.contact_number, sms_message)


def notify_appointment_cancellation(appointment, user, reason=None):
    """Send cancellation notification."""
    message = f'Your {appointment.service_type} appointment on {appointment.appointment_date.strftime("%B %d, %Y")} has been cancelled.'
    if reason:
        message += f' Reason: {reason}'
    
    create_notification(
        user_id=user.id,
        type='appointment_cancelled',
        title='Appointment Cancelled',
        message=message,
        link=f'/appointments/book'
    )
    
    email_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Appointment Cancelled</h2>
            <p>Dear {user.first_name},</p>
            <p>{message}</p>
            <p>Please book a new appointment if needed.</p>
            <p><strong>ISUFST CareHub</strong></p>
        </body>
    </html>
    """
    send_email(user.email, 'Appointment Cancelled', email_body)


# ──────────────────────────────────────────────
#  Waitlist Notifications
# ──────────────────────────────────────────────

def notify_waitlist_slot_available(waitlist_entry, user):
    """Notify student that a slot opened up."""
    create_notification(
        user_id=user.id,
        type='waitlist_slot_available',
        title='Appointment Slot Available!',
        message=f'A slot for {waitlist_entry.service_type} on {waitlist_entry.preferred_date.strftime("%B %d, %Y")} is now available. Book now!',
        link='/appointments/book'
    )
    
    # SMS for immediate notification
    if hasattr(user, 'student_profile') and user.student_profile and user.student_profile.contact_number:
        sms_message = f"ISUFST: A slot for {waitlist_entry.service_type} on {waitlist_entry.preferred_date.strftime('%m/%d/%Y')} is available! Book now at carehub.isufst.edu.ph"
        send_sms(user.student_profile.contact_number, sms_message)


# ──────────────────────────────────────────────
#  Reservation Notifications
# ──────────────────────────────────────────────

def notify_reservation_ready(reservation, user):
    """Notify student that their medicine reservation is ready for pickup."""
    create_notification(
        user_id=user.id,
        type='reservation_ready',
        title='Medicine Ready for Pickup',
        message=f'Your reserved {reservation.medicine_name} ({reservation.quantity} pcs) is ready. Pick up at the clinic.',
        link='/reservations/my'
    )
    
    email_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Medicine Ready for Pickup</h2>
            <p>Dear {user.first_name},</p>
            <p>Your medicine reservation is ready:</p>
            <ul>
                <li><strong>Medicine:</strong> {reservation.medicine_name}</li>
                <li><strong>Quantity:</strong> {reservation.quantity}</li>
            </ul>
            <p>Please pick up at the clinic during office hours. Bring your student ID.</p>
            <p><strong>ISUFST CareHub</strong></p>
        </body>
    </html>
    """
    send_email(user.email, 'Medicine Ready - ISUFST CareHub', email_body)


# ──────────────────────────────────────────────
#  Medicine Expiry Alerts
# ──────────────────────────────────────────────

def notify_expiring_medicines(admin_users, expiring_items):
    """Send weekly alert about expiring medicines to admins."""
    for admin in admin_users:
        items_list = '<ul>'
        for item in expiring_items:
            days_left = (item.expiry_date - datetime.now().date()).days
            items_list += f'<li>{item.name} (Batch: {item.batch_number}) - Expires in {days_left} days</li>'
        items_list += '</ul>'
        
        email_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Medicine Expiry Alert</h2>
                <p>Dear {admin.first_name},</p>
                <p>The following medicines are expiring soon:</p>
                {items_list}
                <p>Please take necessary action.</p>
                <p><strong>ISUFST CareHub Automated Alert</strong></p>
            </body>
        </html>
        """
        send_email(admin.email, 'Medicine Expiry Alert - Action Required', email_body)


def init_notification_service(app):
    """Initialize notification service with Flask app."""
    mail.init_app(app)
    
    # Configure Flask-Mail
    app.config.setdefault('MAIL_SERVER', os.environ.get('MAIL_SERVER', 'smtp.gmail.com'))
    app.config.setdefault('MAIL_PORT', int(os.environ.get('MAIL_PORT', 587)))
    app.config.setdefault('MAIL_USE_TLS', os.environ.get('MAIL_USE_TLS', 'True') == 'True')
    app.config.setdefault('MAIL_USERNAME', os.environ.get('MAIL_USERNAME'))
    app.config.setdefault('MAIL_PASSWORD', os.environ.get('MAIL_PASSWORD'))
    app.config.setdefault('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@isufst.edu.ph'))
