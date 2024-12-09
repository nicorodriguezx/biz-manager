from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import admin
from ..models import read_json, write_json
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
from ..utils.dates import get_range_type, get_date_range

@admin.route('/products', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def manage_products():
    if not current_user.is_admin:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.user_dashboard'))
        
    if request.method == 'GET':
        products = read_json('products.json')
        return render_template('admin/products.html', products=products)
        
    elif request.method == 'POST':
        try:
            data = request.json
            products = read_json('products.json')
            
            # Get next available product_id
            next_id = max([p['product_id'] for p in products], default=0) + 1
            
            new_product = {
                'product_id': next_id,
                'name': data['name'],
                'price': float(data['price']),
                'min_stock': int(data.get('min_stock', 0)),
                'description': data.get('description', '')
            }
            
            products.append(new_product)
            write_json('products.json', products)
            
            return {'success': True, 'product': new_product}
        except Exception as e:
            return {'success': False, 'error': str(e)}, 400
            
    elif request.method == 'PUT':
        try:
            data = request.json
            products = read_json('products.json')
            
            product_id = int(data['product_id'])
            for product in products:
                if product['product_id'] == product_id:
                    product['name'] = data['name']
                    product['price'] = float(data['price'])
                    product['min_stock'] = int(data.get('min_stock', product.get('min_stock', 0)))
                    product['description'] = data.get('description', product.get('description', ''))
                    break
            
            write_json('products.json', products)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}, 400
            
    elif request.method == 'DELETE':
        try:
            product_id = int(request.json['product_id'])
            products = read_json('products.json')
            
            # Check if product is in use in any transaction
            transactions = read_json('transactions.json')
            for transaction in transactions:
                for detail in transaction['details']:
                    if detail['product_id'] == product_id:
                        return {
                            'success': False, 
                            'error': 'No se puede eliminar un producto que ya ha sido utilizado en transacciones.'
                        }, 400
            
            products = [p for p in products if p['product_id'] != product_id]
            write_json('products.json', products)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}, 400 

@admin.route('/admin_board')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.user_dashboard'))
        
    return render_template('admin/admin_board.html') 

@admin.route('/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.user_dashboard'))
        
    users = read_json('users.json')
    return render_template('admin/users.html', users=users)

@admin.route('/users/<int:user_id>', methods=['PUT', 'DELETE'])
@login_required
def update_user(user_id):
    if not current_user.is_admin:
        return {"error": "Acceso no autorizado"}, 403
        
    try:
        users = read_json('users.json')
        user = next((u for u in users if u['user_id'] == user_id), None)
        if not user:
            return {"error": "Usuario no encontrado"}, 404

        if request.method == 'DELETE':
            # Don't allow deleting self
            if user_id == current_user.user_id:
                return {"error": "No puede eliminarse a sí mismo"}, 400
            user['exists'] = 'false'
            write_json('users.json', users)
            return {"success": True}
            
        data = request.json
        
        # Update basic info
        if 'username' in data:
            user['username'] = data['username']
            
        if 'role' in data:
            old_role = user['role']
            new_role = data['role']
            user['role'] = new_role
            
            # Handle commission rate when changing roles
            if old_role == 'admin' and new_role == 'user':
                user['commission_rate'] = float(data.get('commission_rate', 0.10))
            elif old_role == 'user' and new_role == 'admin':
                user.pop('commission_rate', None)
            
        # Update commission rate (only for users)
        if 'commission_rate' in data and user['role'] == 'user':
            user['commission_rate'] = float(data['commission_rate'])
            
        # Update password if provided
        if 'password' in data:
            user['password_hash'] = generate_password_hash(data['password'])
            
        write_json('users.json', users)
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}, 400 

@admin.route('/reports', methods=['GET'])
@login_required
def sales_reports():
    if not current_user.is_admin:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.user_dashboard'))
    
    # Get filter parameters with today as default
    today = date.today().isoformat()
    start_date = request.args.get('start_date', today)
    end_date = request.args.get('end_date', today)
    selected_range = get_range_type(start_date, end_date)
    vendor_id = request.args.get('vendor_id')
    
    # Get all users for the vendor filter
    users = read_json('users.json')
    vendors = [u for u in users if u.get('role') == 'user' and u.get('exists') != 'false']
    
    try:
        # Get sales summaries
        sales_summaries = read_json('sales_summaries.json')
        
        # Apply filters
        if start_date:
            sales_summaries = [s for s in sales_summaries if s['date'] >= start_date]
        if end_date:
            sales_summaries = [s for s in sales_summaries if s['date'] <= end_date]
        if vendor_id:
            vendor_id = int(vendor_id)
            sales_summaries = [s for s in sales_summaries if s['user_id'] == vendor_id]
            
        # Calculate totals
        total_sales = sum(s['total_sales'] for s in sales_summaries)
        total_commission = sum(s['commission'] for s in sales_summaries)
        
        return render_template(
            'admin/reports.html',
            vendors=vendors,
            summaries=sales_summaries,
            total_sales=total_sales,
            total_commission=total_commission,
            selected_vendor=vendor_id,
            start_date=start_date,
            end_date=end_date,
            selected_range=selected_range
        )
        
    except FileNotFoundError:
        return render_template(
            'admin/reports.html',
            vendors=vendors,
            summaries=[],
            total_sales=0,
            total_commission=0,
            selected_vendor=vendor_id,
            start_date=start_date,
            end_date=end_date,
            selected_range=selected_range
        ) 

@admin.route('/stock')
@login_required
def view_stock():
    if not current_user.is_admin:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.user_dashboard'))
    
    today = date.today().isoformat()
    start_date = request.args.get('start_date', today)
    end_date = request.args.get('end_date', today)
    selected_range = get_range_type(start_date, end_date)
    
    try:
        purchases = read_json('stock_purchases.json')
        transactions = read_json('transactions.json')
        transaction_details = read_json('transaction_details.json')
        products = read_json('products.json')
        
        # Filter by period
        period_purchases = [p for p in purchases if start_date <= p['date'] <= end_date]
        period_transactions = [t for t in transactions if start_date <= t['timestamp'].split('T')[0] <= end_date]
        
        stock = {}
        for product in products:
            pid = product['product_id']
            stock[pid] = {
                'product': product,
                'current': 0,  # Will be calculated from all-time data
                'period_purchased': 0,  # Only for selected period
                'period_sold': 0  # Only for selected period
            }
        
        # Calculate period purchases
        for purchase in period_purchases:
            pid = purchase['product_id']
            stock[pid]['period_purchased'] += purchase['quantity']
        
        # Calculate period sales
        for transaction in period_transactions:
            details = [d for d in transaction_details if d['transaction_id'] == transaction['transaction_id']]
            for detail in details:
                pid = detail['product_id']
                if transaction['type'] == 'extract':
                    stock[pid]['period_sold'] += detail['quantity']
                else:  # return
                    stock[pid]['period_sold'] -= detail['quantity']
        
        # Calculate current stock (using all-time data)
        all_purchases = purchases
        all_transactions = transactions
        
        for purchase in all_purchases:
            pid = purchase['product_id']
            stock[pid]['current'] += purchase['quantity']
            
        for transaction in all_transactions:
            details = [d for d in transaction_details if d['transaction_id'] == transaction['transaction_id']]
            for detail in details:
                pid = detail['product_id']
                if transaction['type'] == 'extract':
                    stock[pid]['current'] -= detail['quantity']
                else:  # return
                    stock[pid]['current'] += detail['quantity']
        
        # Calculate total value of current stock
        total_value = sum(
            stock[pid]['current'] * stock[pid]['product']['price']
            for pid in stock
        )
        
        return render_template(
            'admin/stock.html',
            stock=stock,
            start_date=start_date,
            end_date=end_date,
            selected_range=selected_range,
            total_value=total_value
        )
        
    except FileNotFoundError:
        return render_template(
            'admin/stock.html',
            stock={},
            start_date=start_date,
            end_date=end_date,
            selected_range=selected_range,
            total_value=0
        )

@admin.route('/purchases', methods=['GET', 'POST'])
@login_required
def manage_purchases():
    if not current_user.is_admin:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.user_dashboard'))
        
    if request.method == 'POST':
        try:
            data = request.json
            purchases = read_json('stock_purchases.json')
            
            # Create new purchase
            new_purchase = {
                'purchase_id': len(purchases) + 1,
                'date': date.today().isoformat(),
                'product_id': int(data['product_id']),
                'quantity': int(data['quantity']),
                'unit_cost': float(data['unit_cost'])
            }
            
            purchases.append(new_purchase)
            write_json('stock_purchases.json', purchases)
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}, 400
            
    # GET request
    products = read_json('products.json')
    return render_template('admin/purchases.html', products=products) 