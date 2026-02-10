"""
Inventory management blueprint for ISUFST CareHub.
Handles medicine and equipment inventory CRUD operations.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from models import db, Inventory

inventory = Blueprint('inventory', __name__, url_prefix='/inventory')


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


@inventory.route('/')
@login_required
@require_staff
def list_inventory():
    """List all inventory items."""
    items = Inventory.query.order_by(Inventory.expiry_date.asc()).all()
    return render_template('inventory.html', items=items)


@inventory.route('/add', methods=['GET', 'POST'])
@login_required
@require_staff
def add():
    """Add new inventory item."""
    if request.method == 'POST':
        name = request.form.get('name')
        batch_number = request.form.get('batch_number')
        category = request.form.get('category')
        quantity = int(request.form.get('quantity'))
        expiry_date_str = request.form.get('expiry_date')
        
        expiry_date = None
        if expiry_date_str:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        
        item = Inventory(
            name=name,
            batch_number=batch_number,
            category=category,
            quantity=quantity,
            expiry_date=expiry_date
        )
        db.session.add(item)
        db.session.commit()
        
        flash(f'{name} added to inventory.', 'success')
        return redirect(url_for('inventory.list_inventory'))
    
    return render_template('inventory_form.html', item=None)


@inventory.route('/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
@require_staff
def edit(item_id):
    """Edit an inventory item."""
    item = Inventory.query.get_or_404(item_id)
    
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.batch_number = request.form.get('batch_number')
        item.category = request.form.get('category')
        item.quantity = int(request.form.get('quantity'))
        
        expiry_date_str = request.form.get('expiry_date')
        if expiry_date_str:
            item.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        
        db.session.commit()
        
        flash(f'{item.name} updated successfully.', 'success')
        return redirect(url_for('inventory.list_inventory'))
    
    return render_template('inventory_form.html', item=item)


@inventory.route('/<int:item_id>/delete', methods=['POST'])
@login_required
@require_staff
def delete(item_id):
    """Delete an inventory item."""
    item = Inventory.query.get_or_404(item_id)
    
    db.session.delete(item)
    db.session.commit()
    
    flash(f'{item.name} deleted from inventory.', 'success')
    return redirect(url_for('inventory.list_inventory'))


# API Endpoints
@inventory.route('/api/expiring', methods=['GET'])
@login_required
def api_expiring():
    """Get count of items expiring soon."""
    expiring_items = Inventory.query.filter(
        Inventory.category == 'Medicine',
        Inventory.quantity > 0
    ).all()
    
    count = sum(1 for item in expiring_items if item.is_expiring_soon())
    
    return jsonify({'count': count})
