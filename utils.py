"""
Utility functions for ISUFST CareHub clinic business logic.
"""
from datetime import date, time
from models import db, Appointment, Inventory, Queue


# ──────────────────────────────────────────────
#  Conflict Detection (Dental/Medical)
# ──────────────────────────────────────────────
def check_availability(appointment_date, start_time, end_time, service_type='Dental'):
    """
    Check if a time slot is available for appointments.
    
    Args:
        appointment_date (date): The date of the appointment
        start_time (time): Start time of the requested slot
        end_time (time): End time of the requested slot
        service_type (str): 'Dental' or 'Medical'
    
    Returns:
        bool: True if the slot is available, False if there's a conflict
    """
    # Query all appointments for the same date and service type
    # that are not cancelled
    existing_appointments = Appointment.query.filter(
        Appointment.appointment_date == appointment_date,
        Appointment.service_type == service_type,
        Appointment.status.in_(['Pending', 'Confirmed', 'Completed'])
    ).all()
    
    # Check for time overlaps
    for appt in existing_appointments:
        # Two time slots overlap if:
        # (start1 < end2) AND (end1 > start2)
        if (start_time < appt.end_time) and (end_time > appt.start_time):
            return False  # Conflict found
    
    return True  # No conflicts, slot is available


# ──────────────────────────────────────────────
#  FIFO Dispensing
# ──────────────────────────────────────────────
def dispense_medicine(medicine_name, quantity_needed):
    """
    Dispense medicine using FIFO logic (oldest batches first).
    
    Args:
        medicine_name (str): Name of the medicine to dispense
        quantity_needed (int): Quantity to dispense
    
    Returns:
        dict: {
            'success': bool,
            'dispensed': int,
            'batches_used': list of dict with batch details,
            'message': str
        }
    """
    # Query inventory for this medicine, sorted by expiry_date (FIFO)
    batches = Inventory.query.filter(
        Inventory.name == medicine_name,
        Inventory.category == 'Medicine',
        Inventory.quantity > 0
    ).order_by(Inventory.expiry_date.asc()).all()
    
    if not batches:
        return {
            'success': False,
            'dispensed': 0,
            'batches_used': [],
            'message': f'Medicine "{medicine_name}" not found in inventory'
        }
    
    # Calculate total available quantity
    total_available = sum(batch.quantity for batch in batches)
    
    if total_available < quantity_needed:
        return {
            'success': False,
            'dispensed': 0,
            'batches_used': [],
            'message': f'Insufficient quantity. Needed: {quantity_needed}, Available: {total_available}'
        }
    
    # Dispense across batches using FIFO
    remaining_needed = quantity_needed
    batches_used = []
    
    for batch in batches:
        if remaining_needed <= 0:
            break
        
        # Determine how much to take from this batch
        quantity_from_batch = min(batch.quantity, remaining_needed)
        
        # Deduct from inventory
        batch.quantity -= quantity_from_batch
        remaining_needed -= quantity_from_batch
        
        # Record batch usage
        batches_used.append({
            'batch_number': batch.batch_number,
            'expiry_date': batch.expiry_date.isoformat(),
            'quantity_dispensed': quantity_from_batch,
            'remaining_in_batch': batch.quantity
        })
    
    # Commit changes to database
    db.session.commit()
    
    return {
        'success': True,
        'dispensed': quantity_needed,
        'batches_used': batches_used,
        'message': f'Successfully dispensed {quantity_needed} units of {medicine_name}'
    }


# ──────────────────────────────────────────────
#  Priority Queue Sorting
# ──────────────────────────────────────────────
def get_next_patient():
    """
    Get the next patient from the queue based on priority.
    
    Priority is determined by:
    1. severity_score (ASC): 1=Emergency, 2=Urgent, 3=Routine
    2. arrival_time (ASC): Earlier arrivals first within same severity
    
    Returns:
        Queue or None: The next patient to serve, or None if queue is empty
    """
    # Query patients with 'Waiting' status, ordered by priority
    next_patient = Queue.query.filter(
        Queue.status == 'Waiting'
    ).order_by(
        Queue.severity_score.asc(),  # Emergency (1) first
        Queue.arrival_time.asc()     # Then earliest arrival
    ).first()
    
    return next_patient


# ──────────────────────────────────────────────
#  Helper: Get Priority Queue Summary
# ──────────────────────────────────────────────
def get_queue_summary():
    """
    Get a summary of the current queue status.
    
    Returns:
        dict: Summary with counts by severity level
    """
    waiting_patients = Queue.query.filter(Queue.status == 'Waiting').all()
    
    summary = {
        'total_waiting': len(waiting_patients),
        'emergency': len([p for p in waiting_patients if p.severity_score == 1]),
        'urgent': len([p for p in waiting_patients if p.severity_score == 2]),
        'routine': len([p for p in waiting_patients if p.severity_score == 3]),
        'next_patient': get_next_patient()
    }
    
    return summary
