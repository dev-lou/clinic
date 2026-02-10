"""
Medicine reservation blueprint for ISUFST CareHub.
Handles public medicine viewing and reservation system.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone
from models import db, Inventory, MedicineReservation

reservations = Blueprint('reservations', __name__, url_prefix='/reservations')


@reservations.route('/medicines')
def view_medicines():
    """Public page showing available medicines."""
    medicines = Inventory.query.filter(
        Inventory.category == 'Medicine',
        Inventory.quantity > 0
    ).order_by(Inventory.name.asc()).all()
    
    return render_template('medicines.html', medicines=medicines)


@reservations.route('/reserve/<int:medicine_id>', methods=['POST'])
@login_required
def reserve_medicine(medicine_id):
    """Reserve a medicine for pickup."""
    if current_user.role != 'student':
        flash('Only students can reserve medicines.', 'error')
        return redirect(url_for('reservations.view_medicines'))
    
    medicine = Inventory.query.get_or_404(medicine_id)
    
    if medicine.quantity <= 0:
        flash('This medicine is currently out of stock.', 'error')
        return redirect(url_for('reservations.view_medicines'))
    
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > medicine.quantity:
        flash(f'Only {medicine.quantity} units available.', 'error')
        return redirect(url_for('reservations.view_medicines'))
    
    # Create reservation
    reservation = MedicineReservation(
        student_id=current_user.id,
        medicine_name=medicine.name,
        quantity=quantity,
        status='Reserved'
    )
    db.session.add(reservation)
    db.session.commit()
    
    flash(f'Successfully reserved {quantity} unit(s) of {medicine.name}. You can pick it up anytime during clinic hours!', 'success')
    return redirect(url_for('reservations.my_reservations'))


@reservations.route('/my')
@login_required
def my_reservations():
    """View student's medicine reservations."""
    if current_user.role != 'student':
        flash('Only students can view reservations.', 'error')
        return redirect(url_for('index'))
    
    reservations = MedicineReservation.query.filter_by(
        student_id=current_user.id
    ).order_by(MedicineReservation.reserved_at.desc()).all()
    
    return render_template('my_reservations.html', reservations=reservations)


@reservations.route('/<int:reservation_id>/cancel', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    """Cancel a medicine reservation."""
    reservation = MedicineReservation.query.get_or_404(reservation_id)
    
    if reservation.student_id != current_user.id:
        flash('You can only cancel your own reservations.', 'error')
        return redirect(url_for('reservations.my_reservations'))
    
    if reservation.status != 'Reserved':
        flash('This reservation cannot be cancelled.', 'error')
        return redirect(url_for('reservations.my_reservations'))
    
    reservation.status = 'Cancelled'
    db.session.commit()
    
    flash('Reservation cancelled successfully.', 'success')
    return redirect(url_for('reservations.my_reservations'))
