"""
Queue management blueprint for ISUFST CareHub.
Handles patient queue operations.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone
from models import db, Queue
from utils import get_next_patient

queue = Blueprint('queue', __name__, url_prefix='/queue')


def require_staff(f):
    """Decorator to require nurse or admin role."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['nurse', 'admin']:
            flash('Access denied. Staff only.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@queue.route('/add', methods=['POST'])
@login_required
@require_staff
def add():
    """Add a patient to the queue."""
    student_name = request.form.get('student_name')
    severity_score = int(request.form.get('severity_score', 3))
    
    new_patient = Queue(
        student_name=student_name,
        severity_score=severity_score,
        status='Waiting'
    )
    db.session.add(new_patient)
    db.session.commit()
    
    flash(f'{student_name} added to queue.', 'success')
    
    # Broadcast update
    from queue_display import broadcast_queue_update
    broadcast_queue_update()
    
    return redirect(url_for('admin'))


@queue.route('/next', methods=['POST'])
@login_required
@require_staff
def call_next():
    """Call the next patient from the queue."""
    next_patient = get_next_patient()
    
    if not next_patient:
        flash('Queue is empty.', 'info')
        return redirect(url_for('admin'))
    
    next_patient.status = 'Serving'
    next_patient.served_at = datetime.now(timezone.utc)
    db.session.commit()
    
    flash(f'Now serving: {next_patient.student_name}', 'success')
    
    # Broadcast update
    from queue_display import broadcast_queue_update
    broadcast_queue_update()
    
    return redirect(url_for('admin'))


@queue.route('/absent/<int:queue_id>', methods=['POST'])
@login_required
@require_staff
def mark_absent(queue_id):
    """Mark a patient as absent."""
    patient = Queue.query.get_or_404(queue_id)
    
    patient.status = 'Absent'
    db.session.commit()
    
    flash(f'{patient.student_name} marked as absent.', 'info')
    
    # Broadcast update
    from queue_display import broadcast_queue_update
    broadcast_queue_update()
    
    return redirect(url_for('admin'))


# API Endpoints
@queue.route('/api/status', methods=['GET'])
@login_required
def api_status():
    """Get current queue status for real-time updates."""
    next_patient = get_next_patient()
    waiting_count = Queue.query.filter_by(status='Waiting').count()
    
    if next_patient:
        return jsonify({
            'next_patient': {
                'id': next_patient.id,
                'name': next_patient.student_name,
                'priority': next_patient.priority_label,
                'arrival_time': next_patient.arrival_time.isoformat()
            },
            'waiting_count': waiting_count
        })
    else:
        return jsonify({
            'next_patient': None,
            'waiting_count': 0
        })
