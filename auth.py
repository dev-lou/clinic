"""
Authentication blueprint for ISUFST CareHub.
Handles login, registration, and logout.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User, StudentProfile

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
        
        # Validation
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
            role='student'
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
    return redirect(url_for('index'))


@auth.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('profile.html', user=current_user)
