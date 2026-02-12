"""
Real-Time Queue Display Board for ISUFST CareHub.
Public-facing TV display with WebSocket support for live updates.
"""
from flask import Blueprint, render_template, jsonify
from flask_socketio import SocketIO, emit
from models import Queue
from datetime import datetime

queue_display = Blueprint('queue_display', __name__, url_prefix='/queue-display')

# SocketIO will be initialized in app.py
# Force threading mode (compatible with Python 3.13 + gunicorn, doesn't need eventlet)
socketio = SocketIO(async_mode='threading')


@queue_display.route('/')
def display():
    """TV-friendly queue display board."""
    return render_template('queue_display.html')


@queue_display.route('/api/current-queue')
def get_current_queue():
    """Get current queue state."""
    waiting = Queue.query.filter_by(status='Waiting').order_by(
        Queue.severity_score.asc(),  # Lower score = higher priority
        Queue.arrival_time.asc()
    ).all()
    
    serving = Queue.query.filter_by(status='Serving').first()
    
    return jsonify({
        'serving': {
            'id': serving.id,
            'name': serving.student_name,
            'priority': serving.priority_label
        } if serving else None,
        'waiting': [{
            'position': idx + 1,
            'id': patient.id,
            'name': patient.student_name,
            'priority': patient.priority_label,
            'wait_time_minutes': int((datetime.now(patient.arrival_time.tzinfo) - patient.arrival_time).total_seconds() / 60)
        } for idx, patient in enumerate(waiting[:10])],  # Show top 10
        'total_waiting': len(waiting),
        'updated_at': datetime.now().isoformat()
    })


def broadcast_queue_update():
    """Broadcast queue update to all connected clients via WebSocket."""
    queue_data = get_current_queue().json
    socketio.emit('queue_update', queue_data, namespace='/queue-display')


# WebSocket event handlers
@socketio.on('connect', namespace='/queue-display')
def handle_connect():
    """Client connected to queue display."""
    print('Client connected to queue display')
    # Send initial queue state
    emit('queue_update', get_current_queue().json)


@socketio.on('disconnect', namespace='/queue-display')
def handle_disconnect():
    """Client disconnected."""
    print('Client disconnected from queue display')
