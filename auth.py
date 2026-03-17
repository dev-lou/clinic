"""
Authentication blueprint for ISUFST CareHub.
Handles login, registration, and logout.
"""
import json
import math
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User, StudentProfile
from supabase_storage import upload_profile_image, delete_profile_image

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and form handler."""
    if current_user.is_authenticated:
        if current_user.role in ['admin', 'nurse']:
            return redirect(url_for('admin'))
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            
            # Redirect based on role
            if user.role in ['admin', 'nurse']:
                return redirect(url_for('admin'))
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page for students."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        student_id_number = request.form.get('student_id_number')
        course = request.form.get('course')
        year_level = request.form.get('year_level')
        contact_number = request.form.get('contact_number')
        blood_type = request.form.get('blood_type')
        allergies = request.form.get('allergies')
        medical_conditions = request.form.get('medical_conditions')
        emergency_contact_name = request.form.get('emergency_contact_name')
        emergency_contact_number = request.form.get('emergency_contact_number')
        signature_data = request.form.get('signature_data')
        
        # Validation
        if not signature_data:
            flash('Please draw your signature.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        if StudentProfile.query.filter_by(student_id_number=student_id_number).first():
            flash('Student ID number already registered.', 'error')
            return render_template('register.html')
        
        # Create user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='student',
            signature_data=signature_data
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Get user.id
        
        # Create student profile
        profile = StudentProfile(
            user_id=user.id,
            student_id_number=student_id_number,
            course=course,
            year_level=int(year_level) if year_level else None,
            contact_number=contact_number,
            blood_type=blood_type,
            allergies=allergies,
            medical_conditions=medical_conditions,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_number=emergency_contact_number
        )
        db.session.add(profile)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')


@auth.route('/logout')
@login_required
def logout():
    """Logout current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page - edit own account."""
    if request.method == 'POST':
        # Handle JSON requests (e.g., signature save)
        if request.is_json:
            data = request.get_json()
            action = data.get('action')
        else:
            action = request.form.get('action')
        
        if action == 'update_info':
            current_user.first_name = request.form.get('first_name')
            current_user.last_name = request.form.get('last_name')
            current_user.email = request.form.get('email')
            
            # Update student profile if exists
            if current_user.role == 'student' and current_user.student_profile:
                profile = current_user.student_profile
                profile.contact_number = request.form.get('contact_number')
                profile.course = request.form.get('course')
                profile.year_level = int(request.form.get('year_level')) if request.form.get('year_level') else None
                profile.blood_type = request.form.get('blood_type')
                profile.allergies = request.form.get('allergies')
                profile.medical_conditions = request.form.get('medical_conditions')
                profile.emergency_contact_name = request.form.get('emergency_contact_name')
                profile.emergency_contact_number = request.form.get('emergency_contact_number')
            
            db.session.commit()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
        
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'error')
            elif len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'error')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password changed successfully.', 'success')
                return redirect(url_for('auth.profile'))
        
        elif action == 'save_signature':
            try:
                # Get signature data from JSON or form
                if request.is_json:
                    signature_data = data.get('signature_data')
                else:
                    signature_data = request.form.get('signature_data')
                
                if signature_data:
                    current_user.signature_data = signature_data
                    db.session.commit()
                    return jsonify({'success': True, 'message': 'Signature saved successfully'})
                return jsonify({'success': False, 'message': 'No signature data provided'}), 400
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        elif action == 'upload_avatar':
            file = request.files.get('avatar')
            if not file or not file.filename:
                flash('No file selected.', 'error')
                return redirect(url_for('auth.profile'))
            try:
                # Delete old image if exists
                if current_user.profile_image_url:
                    delete_profile_image(current_user.profile_image_url)
                # Upload new image
                url = upload_profile_image(file, current_user.id)
                current_user.profile_image_url = url
                db.session.commit()
                flash('Profile photo updated!', 'success')
            except ValueError as e:
                flash(str(e), 'error')
            except Exception as e:
                flash('Failed to upload image. Please try again.', 'error')
            return redirect(url_for('auth.profile'))

        elif action == 'remove_avatar':
            if current_user.profile_image_url:
                delete_profile_image(current_user.profile_image_url)
                current_user.profile_image_url = None
                db.session.commit()
                flash('Profile photo removed.', 'success')
            return redirect(url_for('auth.profile'))
    
    return render_template('profile.html')


@auth.route('/users')
@login_required
def list_users():
    """Admin: List all users."""
    if current_user.role not in ['admin', 'staff']:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('index'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('user_management.html', users=users)


@auth.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Admin: Edit a user."""
    if current_user.role not in ['admin', 'staff']:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_info':
            user.first_name = request.form.get('first_name')
            user.last_name = request.form.get('last_name')
            user.email = request.form.get('email')
            user.role = request.form.get('role')
            user.is_active = request.form.get('is_active') == 'on'
            
            # Update student profile if exists
            if user.role == 'student' and user.student_profile:
                profile = user.student_profile
                profile.student_id_number = request.form.get('student_id_number')
                profile.contact_number = request.form.get('contact_number')
                profile.course = request.form.get('course')
                profile.year_level = int(request.form.get('year_level')) if request.form.get('year_level') else None
                profile.blood_type = request.form.get('blood_type')
                profile.allergies = request.form.get('allergies')
                profile.medical_conditions = request.form.get('medical_conditions')
                profile.emergency_contact_name = request.form.get('emergency_contact_name')
                profile.emergency_contact_number = request.form.get('emergency_contact_number')
            
            db.session.commit()
            flash(f'{user.full_name} updated successfully.', 'success')
            return redirect(url_for('auth.list_users'))
        
        elif action == 'reset_password':
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password != confirm_password:
                flash('Passwords do not match.', 'error')
            elif len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'error')
            else:
                user.set_password(new_password)
                db.session.commit()
                flash(f'Password reset for {user.full_name}.', 'success')
                return redirect(url_for('auth.list_users'))
    
    return render_template('edit_user.html', user=user)


@auth.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Admin: Delete a user."""
    if current_user.role not in ['admin', 'staff']:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Cannot delete your own account.', 'error')
        return redirect(url_for('auth.list_users'))
    
    name = user.full_name
    db.session.delete(user)
    db.session.commit()
    flash(f'{name} deleted successfully.', 'success')
    return redirect(url_for('auth.list_users'))


# ---------------------------------------------------------------------------
# Face Recognition Login
# ---------------------------------------------------------------------------
def _euclidean_distance(desc1, desc2):
    """Calculate euclidean distance between two face descriptor arrays."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(desc1, desc2)))


@auth.route('/enable-face-login', methods=['POST'])
@login_required
def enable_face_login():
    """Save face descriptor for face recognition login."""
    data = request.get_json()
    descriptor = data.get('descriptor')

    if not descriptor or not isinstance(descriptor, list):
        return jsonify({'success': False, 'message': 'Invalid face descriptor'}), 400

    if len(descriptor) != 128:
        return jsonify({'success': False, 'message': 'Invalid descriptor length (expected 128)'}), 400

    current_user.face_descriptor = json.dumps(descriptor)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Face login enabled successfully!'})


@auth.route('/disable-face-login', methods=['POST'])
@login_required
def disable_face_login():
    """Remove face descriptor to disable face login."""
    current_user.face_descriptor = None
    db.session.commit()
    return jsonify({'success': True, 'message': 'Face login disabled.'})


@auth.route('/face-login', methods=['POST'])
def face_login():
    """Authenticate user via face recognition."""
    if current_user.is_authenticated:
        return jsonify({'success': True, 'redirect': url_for('index')})

    data = request.get_json()
    descriptor = data.get('descriptor')

    if not descriptor or not isinstance(descriptor, list) or len(descriptor) != 128:
        return jsonify({'success': False, 'message': 'Invalid face data'}), 400

    # Find all users with face descriptors
    users_with_face = User.query.filter(
        User.face_descriptor.isnot(None),
        User.is_active == True
    ).all()

    if not users_with_face:
        return jsonify({'success': False, 'message': 'No users have face login enabled'}), 404

    best_match = None
    best_distance = float('inf')
    THRESHOLD = 0.6  # face-api.js recommended threshold

    for user in users_with_face:
        try:
            stored = json.loads(user.face_descriptor)
            distance = _euclidean_distance(descriptor, stored)
            if distance < best_distance:
                best_distance = distance
                best_match = user
        except (json.JSONDecodeError, TypeError):
            continue

    if best_match and best_distance < THRESHOLD:
        login_user(best_match, remember=True)
        redirect_url = url_for('admin') if best_match.role in ['admin', 'nurse'] else url_for('index')
        return jsonify({
            'success': True,
            'message': f'Welcome back, {best_match.first_name}!',
            'user': best_match.full_name,
            'redirect': redirect_url,
            'confidence': round((1 - best_distance) * 100, 1)
        })

    return jsonify({
        'success': False,
        'message': 'Face not recognized. Please use email and password to sign in.'
    }), 401


@auth.route('/face-login-status')
@login_required
def face_login_status():
    """Check if current user has face login enabled."""
    return jsonify({
        'enabled': current_user.face_descriptor is not None,
        'has_profile_image': current_user.profile_image_url is not None
    })
