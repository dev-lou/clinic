"""
Medicine reservation blueprint for ISUFST CareHub.
Handles public medicine viewing and reservation system.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from models import db, Inventory, MedicineReservation
from models_extended import MedicineReservationExtended
from advanced_utils import generate_reservation_qr, generate_qr_code

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

    db.session.flush()  # Get reservation.id without committing

    # Generate QR code for reservation check-in
    _, qr_token = generate_reservation_qr(reservation.id)
    reservation_ext = MedicineReservationExtended(
        reservation_id=reservation.id,
        qr_code=qr_token
    )
    db.session.add(reservation_ext)

    db.session.commit()
    
    flash(f'Successfully reserved {quantity} unit(s) of {medicine.name}. You can pick it up anytime during clinic hours!', 'success')
    return redirect(url_for('reservations.my_reservations'))


@reservations.route('/my')
@login_required
def my_reservations():
    """View student's medicine reservations."""
    # Allow all logged-in users for testing
    # if current_user.role != 'student':
    #     flash('Only students can view reservations.', 'error')
    #     return redirect(url_for('index'))
    
    reservations = MedicineReservation.query.filter_by(
        student_id=current_user.id
    ).order_by(MedicineReservation.reserved_at.desc()).all()
    
    return render_template('my_reservations.html', reservations=reservations)


@reservations.route('/api/get-qr/<int:reservation_id>')
@login_required
def get_reservation_qr(reservation_id):
    """Get QR code image for a medicine reservation."""
    import json

    reservation = MedicineReservation.query.get_or_404(reservation_id)

    # Verify access - student can only view their own
    if current_user.role == 'student' and reservation.student_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    ext = MedicineReservationExtended.query.filter_by(reservation_id=reservation_id).first()
    if not ext or not ext.qr_code:
        return jsonify({'error': 'QR code not available'}), 404

    qr_data = json.dumps({
        'type': 'medicine_reservation',
        'reservation_id': reservation_id,
        'token': ext.qr_code,
        'expires': (datetime.now() + timedelta(days=30)).isoformat()
    })

    qr_image = generate_qr_code(qr_data, add_logo=False)

    return jsonify({
        'qr_image': qr_image,
        'reservation': {
            'id': reservation.id,
            'medicine_name': reservation.medicine_name,
            'quantity': reservation.quantity,
            'status': reservation.status,
            'reserved_at': reservation.reserved_at.strftime('%B %d, %Y')
        }
    })


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


# ═══════════ ADMIN ROUTES ═══════════
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


@reservations.route('/admin')
@login_required
@require_staff
def admin_list():
    """Admin view to manage all medicine reservations."""
    filter_status = request.args.get('status', 'all')
    
    query = MedicineReservation.query
    
    if filter_status != 'all':
        query = query.filter_by(status=filter_status)
    
    reservations_list = query.order_by(MedicineReservation.reserved_at.desc()).all()
    
    return render_template('admin_reservations.html', reservations=reservations_list, filter_status=filter_status)


@reservations.route('/admin/<int:reservation_id>/mark-picked-up', methods=['POST'])
@login_required
@require_staff
def admin_mark_picked_up(reservation_id):
    """Admin route to mark reservation as picked up."""
    reservation = MedicineReservation.query.get_or_404(reservation_id)
    
    if reservation.status == 'Reserved':
        reservation.status = 'Picked Up'
        db.session.commit()
        
        # Send notification to student
        from notifications import create_notification
        create_notification(
            user_id=reservation.student_id,
            notif_type='reservation_update',
            title='Medicine Picked Up ✅',
            message=f'Your reservation for {reservation.medicine_name} ({reservation.quantity} unit(s)) has been marked as picked up.',
            link='/reservations/my'
        )
        
        flash(f'Marked as picked up.', 'success')
    else:
        flash('Cannot update status.', 'error')
    
    return redirect(url_for('reservations.admin_list'))


@reservations.route('/api/verify-qr', methods=['POST'])
@login_required
@require_staff
def verify_reservation_qr():
    """Verify QR code for medicine reservation check-in."""
    try:
        import json as json_module

        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        qr_data_json = data.get('qr_data')
        if not qr_data_json:
            return jsonify({'error': 'QR data required'}), 400

        try:
            qr_data = json_module.loads(qr_data_json)
        except json_module.JSONDecodeError as e:
            return jsonify({'error': f'Invalid JSON in QR data: {str(e)}'}), 400

        if 'expires' not in qr_data or 'reservation_id' not in qr_data or 'token' not in qr_data:
            return jsonify({'error': 'QR code missing required fields'}), 400

        expires = datetime.fromisoformat(qr_data['expires'])
        if expires.tzinfo:
            expires = expires.replace(tzinfo=None)

        now = datetime.now()
        if now > expires:
            return jsonify({'error': f'QR code expired on {expires.strftime("%B %d, %Y at %I:%M %p")}'}), 400

        reservation_id = qr_data['reservation_id']
        reservation = MedicineReservation.query.get(reservation_id)
        if not reservation:
            return jsonify({'error': f'Reservation #{reservation_id} not found'}), 404

        if reservation.status != 'Reserved':
            return jsonify({'error': f'Reservation status is {reservation.status}'}), 400

        ext = MedicineReservationExtended.query.filter_by(reservation_id=reservation_id).first()
        if not ext or not ext.qr_code:
            return jsonify({'error': 'Reservation has no QR code generated'}), 400
        if ext.qr_code != qr_data['token']:
            return jsonify({'error': 'Invalid QR code token (does not match)'}), 400

        student = reservation.student
        return jsonify({
            'success': True,
            'type': 'medicine_reservation',
            'student': {
                'id': student.id,
                'name': f'{student.first_name} {student.last_name}',
                'email': student.email,
                'student_id': student.student_profile.student_id_number if student.student_profile else 'N/A'
            },
            'reservation': {
                'id': reservation.id,
                'medicine_name': reservation.medicine_name,
                'quantity': reservation.quantity,
                'status': reservation.status,
                'reserved_at': reservation.reserved_at.strftime('%B %d, %Y')
            }
        })
    except Exception as e:
        import traceback
        print("=" * 80)
        print("ERROR in verify_reservation_qr endpoint:")
        print(traceback.format_exc())
        print("=" * 80)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

