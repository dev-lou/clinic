"""
Role-Based Access Control (RBAC) System for ISUFST CareHub.
Provides unified permission decorators and permission checking.
"""
from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user
from enum import Enum


class Role(Enum):
    """User roles with hierarchical permissions."""
    STUDENT = 'student'
    NURSE = 'nurse'
    DOCTOR = 'doctor'
    ADMIN = 'admin'


class Permission(Enum):
    """Granular permissions for different actions."""
    # Queue permissions
    VIEW_QUEUE = 'view_queue'
    MANAGE_QUEUE = 'manage_queue'
    
    # Appointment permissions
    BOOK_APPOINTMENT = 'book_appointment'
    VIEW_OWN_APPOINTMENTS = 'view_own_appointments'
    VIEW_ALL_APPOINTMENTS = 'view_all_appointments'
    MANAGE_APPOINTMENTS = 'manage_appointments'
    
    # Medical records permissions
    VIEW_OWN_RECORDS = 'view_own_records'
    VIEW_ALL_RECORDS = 'view_all_records'
    CREATE_CLINIC_VISIT = 'create_clinic_visit'
    
    # Inventory permissions
    VIEW_INVENTORY = 'view_inventory'
    MANAGE_INVENTORY = 'manage_inventory'
    
    # Reservation permissions
    RESERVE_MEDICINE = 'reserve_medicine'
    MANAGE_RESERVATIONS = 'manage_reservations'
    
    # User management
    VIEW_USERS = 'view_users'
    MANAGE_USERS = 'manage_users'
    
    # Analytics
    VIEW_ANALYTICS = 'view_analytics'
    
    # Prescription
    PRESCRIBE_MEDICINE = 'prescribe_medicine'
    
    # Schedule
    MANAGE_SCHEDULE = 'manage_schedule'


# Permission matrix: Role -> Set of permissions
ROLE_PERMISSIONS = {
    Role.STUDENT: {
        Permission.BOOK_APPOINTMENT,
        Permission.VIEW_OWN_APPOINTMENTS,
        Permission.VIEW_OWN_RECORDS,
        Permission.RESERVE_MEDICINE,
    },
    Role.NURSE: {
        Permission.VIEW_QUEUE,
        Permission.MANAGE_QUEUE,
        Permission.VIEW_ALL_APPOINTMENTS,
        Permission.MANAGE_APPOINTMENTS,
        Permission.VIEW_ALL_RECORDS,
        Permission.CREATE_CLINIC_VISIT,
        Permission.VIEW_INVENTORY,
        Permission.MANAGE_RESERVATIONS,
        Permission.VIEW_ANALYTICS,
    },
    Role.DOCTOR: {
        Permission.VIEW_QUEUE,
        Permission.MANAGE_QUEUE,
        Permission.VIEW_ALL_APPOINTMENTS,
        Permission.MANAGE_APPOINTMENTS,
        Permission.VIEW_ALL_RECORDS,
        Permission.CREATE_CLINIC_VISIT,
        Permission.VIEW_INVENTORY,
        Permission.PRESCRIBE_MEDICINE,
        Permission.MANAGE_SCHEDULE,
        Permission.VIEW_ANALYTICS,
    },
    Role.ADMIN: set(Permission),  # Admin has all permissions
}


def has_permission(user, permission):
    """Check if a user has a specific permission."""
    if not user or not user.is_authenticated:
        return False
    
    try:
        user_role = Role(user.role)
    except ValueError:
        return False
    
    return permission in ROLE_PERMISSIONS.get(user_role, set())


def require_permission(*permissions):
    """
    Decorator to require one or more permissions.
    Usage: @require_permission(Permission.MANAGE_QUEUE)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Check if user has at least one of the required permissions
            for permission in permissions:
                if has_permission(current_user, permission):
                    return f(*args, **kwargs)
            
            flash('You do not have permission to access this resource.', 'error')
            return redirect(url_for('index'))
        
        return decorated_function
    return decorator


def require_role(*roles):
    """
    Decorator to require one or more roles.
    Usage: @require_role(Role.NURSE, Role.ADMIN)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            try:
                user_role = Role(current_user.role)
            except ValueError:
                flash('Invalid user role.', 'error')
                return redirect(url_for('index'))
            
            if user_role in roles:
                return f(*args, **kwargs)
            
            flash('Access denied. Insufficient privileges.', 'error')
            return redirect(url_for('index'))
        
        return decorated_function
    return decorator


def require_staff(f):
    """Decorator to require nurse, doctor, or admin role."""
    return require_role(Role.NURSE, Role.DOCTOR, Role.ADMIN)(f)


def require_medical_staff(f):
    """Decorator to require doctor or nurse role (not admin)."""
    return require_role(Role.DOCTOR, Role.NURSE)(f)


def require_admin(f):
    """Decorator to require admin role."""
    return require_role(Role.ADMIN)(f)


# Context processor to make permission checking available in templates
def init_rbac(app):
    """Initialize RBAC system with Flask app."""
    
    @app.context_processor
    def inject_permissions():
        """Make permission utilities available in all templates."""
        return {
            'has_permission': has_permission,
            'Permission': Permission,
            'Role': Role,
        }
