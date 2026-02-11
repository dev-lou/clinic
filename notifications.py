"""
Notifications blueprint for ISUFST CareHub.
Handles notification creation, retrieval, and management.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timezone
from models import db, Notification

notifications = Blueprint('notifications', __name__, url_prefix='/notifications')


# ═══════════ HELPER FUNCTIONS ═══════════

def create_notification(user_id, notif_type, title, message, link=None):
    """Create a new notification for a user.
    
    Args:
        user_id: Target user ID
        notif_type: 'appointment_update', 'reservation_update', 'reminder'
        title: Short notification title
        message: Notification message
        link: Optional URL to navigate to
    """
    notification = Notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        message=message,
        link=link,
        is_read=False
    )
    db.session.add(notification)
    db.session.commit()
    return notification


# ═══════════ API ROUTES ═══════════

@notifications.route('/unread-count')
@login_required
def unread_count():
    """API: Get count of unread notifications for current user."""
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    return jsonify({'count': count})


@notifications.route('/list')
@login_required
def notification_list():
    """API: Get recent notifications for current user."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    notifs = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).limit(per_page).offset((page - 1) * per_page).all()
    
    return jsonify({
        'notifications': [{
            'id': n.id,
            'type': n.type,
            'title': n.title,
            'message': n.message,
            'link': n.link,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat() if n.created_at else None,
            'time_ago': _time_ago(n.created_at)
        } for n in notifs]
    })


@notifications.route('/mark-read', methods=['POST'])
@login_required
def mark_read():
    """API: Mark notification(s) as read."""
    data = request.get_json() or {}
    notif_id = data.get('id')
    mark_all = data.get('all', False)
    
    if mark_all:
        Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).update({'is_read': True})
        db.session.commit()
        return jsonify({'success': True, 'message': 'All notifications marked as read'})
    
    if notif_id:
        notif = Notification.query.filter_by(
            id=notif_id,
            user_id=current_user.id
        ).first()
        if notif:
            notif.is_read = True
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid request'}), 400


def _time_ago(dt):
    """Convert datetime to human-readable 'time ago' string."""
    if not dt:
        return ''
    
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    seconds = int(diff.total_seconds())
    
    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        mins = seconds // 60
        return f'{mins}m ago'
    elif seconds < 86400:
        hours = seconds // 3600
        return f'{hours}h ago'
    elif seconds < 604800:
        days = seconds // 86400
        return f'{days}d ago'
    else:
        return dt.strftime('%b %d')
