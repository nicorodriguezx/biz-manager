# Standard library imports
from datetime import datetime, date

# Third party imports
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

# Local imports
from . import admin
from ..models import read_json, write_json
from ..utils.dates import get_range_type

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
            
    # Add a default return for unexpected methods
    return {'success': False, 'error': 'Método no permitido'}, 405 

@admin.route('/admin_board')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.user_dashboard'))
        
    return render_template('admin/admin_board.html') 

@admin.route('/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.user_dashboard'))
        
    if request.method == 'GET':
        users = read_json('users.json')
        return render_template('admin/users.html', users=users)
        
    # POST request
    try:
        data = request.json
        print('Received data:', data)  # Debug log
        
        users = read_json('users.json')
        
        if any(user['username'] == data['username'] for user in users):
            print('Username already exists')  # Debug log
            return {'success': False, 'error': 'El nombre de usuario ya existe'}, 400
        
        # Use generator expression for max()
        next_id = max((u['user_id'] for u in users), default=0) + 1
        
        new_user = {
            'user_id': next_id,
            'username': data['username'],
            'password': generate_password_hash(data['password']),
            'role': data['role'],
            'exists': 'true'
        }
        
        if data['role'] == 'user':
            new_user['commission_rate'] = float(data.get('commission_rate', 0))
        
        print('New user data:', new_user)  # Debug log
        
        users.append(new_user)
        write_json('users.json', users)
        
        return {'success': True, 'user': new_user}
    except Exception as e:
        print('Error:', str(e))  # Debug log
        return {'success': False, 'error': str(e)}, 400

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
        purchase_details = read_json('purchase_details.json')
        for purchase in period_purchases:
            details = [d for d in purchase_details if d['purchase_id'] == purchase['purchase_id']]
            for detail in details:
                pid = detail['product_id']
                stock[pid]['period_purchased'] += detail['quantity']
        
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
        for purchase in all_purchases:
            details = [d for d in purchase_details if d['purchase_id'] == purchase['purchase_id']]
            for detail in details:
                pid = detail['product_id']
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
            purchases = read_json('purchases.json')
            purchase_details = read_json('purchase_details.json')
            
            # Calculate total cost
            total_cost = sum(float(item['quantity']) * float(item['unit_cost']) 
                           for item in data['items'])
            
            # Create new purchase
            purchase_id = len(purchases) + 1
            new_purchase = {
                'purchase_id': purchase_id,
                'date': date.today().isoformat(),
                'created_at': datetime.now().isoformat(),
                'total_cost': total_cost
            }
            
            # Create purchase details
            next_detail_id = len(purchase_details) + 1
            new_details = []
            for item in data['items']:
                detail = {
                    'detail_id': next_detail_id,
                    'purchase_id': purchase_id,
                    'product_id': int(item['product_id']),
                    'quantity': int(item['quantity']),
                    'unit_cost': float(item['unit_cost'])
                }
                new_details.append(detail)
                next_detail_id += 1
            
            # Save everything
            purchases.append(new_purchase)
            purchase_details.extend(new_details)
            
            write_json('purchases.json', purchases)
            write_json('purchase_details.json', purchase_details)
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}, 400
            
    # GET request
    products = read_json('products.json')
    return render_template('admin/purchases.html', products=products) 

@admin.route('/expenses', methods=['GET', 'POST'])
@login_required
def manage_expenses():
    if not current_user.is_admin:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.user_dashboard'))
        
    if request.method == 'POST':
        try:
            data = request.json
            expenses = read_json('expenses.json')
            
            new_expense = {
                'expense_id': len(expenses) + 1,
                'date': data['date'],
                'amount': float(data['amount']),
                'description': data.get('description', ''),
                'created_at': datetime.now().isoformat()
            }
            
            expenses.append(new_expense)
            write_json('expenses.json', expenses)
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}, 400
            
    # GET request
    expenses = read_json('expenses.json')
    # Sort by date, most recent first
    expenses.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template(
        'admin/expenses.html',
        expenses=expenses,
        today=date.today().isoformat()
    ) 

@admin.route('/view_purchases')
@login_required
def view_purchases():
    if not current_user.is_admin:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.user_dashboard'))
    
    today = date.today().isoformat()
    start_date = request.args.get('start_date', today)
    end_date = request.args.get('end_date', today)
    selected_range = get_range_type(start_date, end_date)
    
    try:
        purchases = read_json('purchases.json')
        purchase_details = read_json('purchase_details.json')
        products = read_json('products.json')
        
        # Filter by period
        purchases = [p for p in purchases if start_date <= p['date'] <= end_date]
        
        # Sort by date, most recent first
        purchases.sort(key=lambda x: x['date'], reverse=True)
        
        # Add details with product names to each purchase
        for purchase in purchases:
            details = [d for d in purchase_details if d['purchase_id'] == purchase['purchase_id']]
            for detail in details:
                product = next((p for p in products if p['product_id'] == detail['product_id']), None)
                detail['product_name'] = product['name'] if product else 'Producto no encontrado'
            purchase['details'] = details
        
        return render_template(
            'admin/view_purchases.html',
            purchases=purchases,
            total_spent=sum(p['total_cost'] for p in purchases),
            start_date=start_date,
            end_date=end_date,
            selected_range=selected_range
        )
        
    except FileNotFoundError:
        return render_template(
            'admin/view_purchases.html',
            purchases=[],
            total_spent=0,
            start_date=start_date,
            end_date=end_date,
            selected_range=selected_range
        ) 

@admin.route('/transactions')
@login_required
def view_transactions():
    if not current_user.is_admin:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.user_dashboard'))
    
    today = date.today().isoformat()
    start_date = request.args.get('start_date', today)
    end_date = request.args.get('end_date', today)
    selected_range = get_range_type(start_date, end_date)
    vendor_id = request.args.get('vendor_id')
    
    try:
        transactions = read_json('transactions.json')
        transaction_details = read_json('transaction_details.json')
        products = read_json('products.json')
        users = read_json('users.json')
        
        # Get vendors for filter
        vendors = [u for u in users if u.get('role') == 'user' and u.get('exists') != 'false']
        
        # Filter transactions by date
        transactions = [t for t in transactions if start_date <= t['timestamp'].split('T')[0] <= end_date]
        
        # Filter by vendor if selected
        if vendor_id:
            vendor_id = int(vendor_id)
            transactions = [t for t in transactions if t['user_id'] == vendor_id]
        
        # Sort by date, most recent first
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Add details and username to each transaction
        for transaction in transactions:
            # Add username
            user = next((u for u in users if u['user_id'] == transaction['user_id']), None)
            transaction['username'] = user['username'] if user else 'Usuario desconocido'
            
            # Add details with product names
            details = [d for d in transaction_details if d['transaction_id'] == transaction['transaction_id']]
            for detail in details:
                product = next((p for p in products if p['product_id'] == detail['product_id']), None)
                detail['product_name'] = product['name'] if product else 'Producto no encontrado'
            transaction['details'] = details
        
        return render_template(
            'admin/view_transactions.html',
            transactions=transactions,
            vendors=vendors,
            selected_vendor=vendor_id,
            start_date=start_date,
            end_date=end_date,
            selected_range=selected_range
        )
        
    except FileNotFoundError:
        return render_template(
            'admin/view_transactions.html',
            transactions=[],
            vendors=[],
            selected_vendor=vendor_id,
            start_date=start_date,
            end_date=end_date,
            selected_range=selected_range
        ) 

@admin.route('/balance')
@login_required
def view_balance():
    if not current_user.is_admin:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.user_dashboard'))
    
    # Get date parameters first
    today = date.today().isoformat()
    start_date = request.args.get('start_date', today)
    end_date = request.args.get('end_date', today)
    selected_range = get_range_type(start_date, end_date)
    
    try:
        # Load all required data
        users = read_json('users.json')
        products = read_json('products.json')
        purchase_details = read_json('purchase_details.json')
        sales = [s for s in read_json('sales_summaries.json') if start_date <= s['date'] <= end_date]
        period_purchases = [p for p in read_json('purchases.json') if start_date <= p['date'] <= end_date]
        period_expenses = [e for e in read_json('expenses.json') if start_date <= e['date'] <= end_date]
        
        # Calculate totals for summary
        total_sales = sum(s['total_sales'] for s in sales)
        total_commissions = sum(s['commission'] for s in sales)
        total_purchases = sum(p['total_cost'] for p in period_purchases)
        total_expenses = sum(e['amount'] for e in period_expenses)
        total_balance = total_sales - total_commissions - total_purchases - total_expenses
        
        # Group data based on selected range
        grouped_balance = []
        
        if selected_range == 'today':
            # Show single day total
            day_total = {
                'sales': sum(s['total_sales'] for s in sales),
                'purchases': sum(p['total_cost'] for p in period_purchases),
                'expenses': sum(e['amount'] for e in period_expenses)
            }
            
            grouped_balance = [{
                'period': 'Hoy',
                'date': start_date,
                'sales': day_total['sales'],
                'commissions': sum(s['commission'] for s in sales),
                'purchases': day_total['purchases'],
                'expenses': day_total['expenses'],
                'balance': day_total['sales'] - day_total['purchases'] - day_total['expenses'],
                'sales_details': [{
                    'date': sale['date'],
                    'username': next((u['username'] for u in users if u['user_id'] == sale['user_id']), 'Usuario desconocido'),
                    'total_sales': sale['total_sales']
                } for sale in sales],
                'commission_details': [{
                    'date': sale['date'],
                    'username': next((u['username'] for u in users if u['user_id'] == sale['user_id']), 'Usuario desconocido'),
                    'commission': sale['commission']
                } for sale in sales],
                'purchases_details': [{
                    'date': purchase['date'],
                    'total_cost': purchase['total_cost'],
                    'products': [p['name'] for p in products if p['product_id'] in [d['product_id'] for d in purchase_details if d['purchase_id'] == purchase['purchase_id']]],
                    'products_details': [
                        {
                            'name': next((p['name'] for p in products if p['product_id'] == detail['product_id']), 'Producto no encontrado'),
                            'quantity': detail['quantity'],
                            'unit_cost': detail['unit_cost']
                        }
                        for detail in purchase_details
                        if detail['purchase_id'] == purchase['purchase_id']
                    ]
                } for purchase in period_purchases],
                'expenses_details': period_expenses
            }]
            
        elif selected_range == 'last-7':
            # Show one card for the 7-day period
            period_total = {
                'sales': sum(s['total_sales'] for s in sales),
                'purchases': sum(p['total_cost'] for p in period_purchases),
                'expenses': sum(e['amount'] for e in period_expenses)
            }
            
            grouped_balance = [{
                'period': 'Últimos 7 días',
                'date': end_date,  # Use end_date for sorting
                'sales': period_total['sales'],
                'commissions': sum(s['commission'] for s in sales),
                'purchases': period_total['purchases'],
                'expenses': period_total['expenses'],
                'balance': period_total['sales'] - period_total['purchases'] - period_total['expenses'],
                'sales_details': [{
                    'date': sale['date'],
                    'username': next((u['username'] for u in users if u['user_id'] == sale['user_id']), 'Usuario desconocido'),
                    'total_sales': sale['total_sales']
                } for sale in sales],
                'commission_details': [{
                    'date': sale['date'],
                    'username': next((u['username'] for u in users if u['user_id'] == sale['user_id']), 'Usuario desconocido'),
                    'commission': sale['commission']
                } for sale in sales],
                'purchases_details': [{
                    'date': purchase['date'],
                    'total_cost': purchase['total_cost'],
                    'products': [p['name'] for p in products if p['product_id'] in [d['product_id'] for d in purchase_details if d['purchase_id'] == purchase['purchase_id']]],
                    'products_details': [
                        {
                            'name': next((p['name'] for p in products if p['product_id'] == detail['product_id']), 'Producto no encontrado'),
                            'quantity': detail['quantity'],
                            'unit_cost': detail['unit_cost']
                        }
                        for detail in purchase_details
                        if detail['purchase_id'] == purchase['purchase_id']
                    ]
                } for purchase in period_purchases],
                'expenses_details': period_expenses
            }]
            
        elif selected_range == 'this-month':
            # Group by month
            months = {}
            for sale in sales:
                month_date = datetime.strptime(sale['date'], '%Y-%m-%d')
                month_key = month_date.strftime('%Y-%m')
                month_name = month_date.strftime('%B %Y').capitalize()
                
                if month_key not in months:
                    months[month_key] = {
                        'name': month_name,
                        'sales': 0,
                        'commissions': 0,
                        'purchases': 0,
                        'expenses': 0,
                        'date': month_date.strftime('%Y-%m-%d'),
                        'sales_details': [],
                        'commission_details': [],
                        'purchases_details': [],
                        'expenses_details': []
                    }
                months[month_key]['sales'] += sale['total_sales']
                months[month_key]['commissions'] += sale['commission']
                months[month_key]['sales_details'].append({
                    'date': sale['date'],
                    'username': next((u['username'] for u in users if u['user_id'] == sale['user_id']), 'Usuario desconocido'),
                    'total_sales': sale['total_sales']
                })
                months[month_key]['commission_details'].append({
                    'date': sale['date'],
                    'username': next((u['username'] for u in users if u['user_id'] == sale['user_id']), 'Usuario desconocido'),
                    'commission': sale['commission']
                })
            
            for purchase in period_purchases:
                month_date = datetime.strptime(purchase['date'], '%Y-%m-%d')
                month_key = month_date.strftime('%Y-%m')
                month_name = month_date.strftime('%B %Y').capitalize()
                
                if month_key not in months:
                    months[month_key] = {
                        'name': month_name,
                        'sales': 0,
                        'commissions': 0,
                        'purchases': 0,
                        'expenses': 0,
                        'date': month_date.strftime('%Y-%m-%d'),
                        'sales_details': [],
                        'commission_details': [],
                        'purchases_details': [],
                        'expenses_details': []
                    }
                months[month_key]['purchases'] += purchase['total_cost']
                months[month_key]['purchases_details'].append({
                    'date': purchase['date'],
                    'total_cost': purchase['total_cost'],
                    'products': [p['name'] for p in products if p['product_id'] in [d['product_id'] for d in purchase_details if d['purchase_id'] == purchase['purchase_id']]],
                    'products_details': [
                        {
                            'name': next((p['name'] for p in products if p['product_id'] == detail['product_id']), 'Producto no encontrado'),
                            'quantity': detail['quantity'],
                            'unit_cost': detail['unit_cost']
                        }
                        for detail in purchase_details
                        if detail['purchase_id'] == purchase['purchase_id']
                    ]
                })
            
            for expense in period_expenses:
                month_date = datetime.strptime(expense['date'], '%Y-%m-%d')
                month_key = month_date.strftime('%Y-%m')
                month_name = month_date.strftime('%B %Y').capitalize()
                
                if month_key not in months:
                    months[month_key] = {
                        'name': month_name,
                        'sales': 0,
                        'commissions': 0,
                        'purchases': 0,
                        'expenses': 0,
                        'date': month_date.strftime('%Y-%m-%d'),
                        'sales_details': [],
                        'commission_details': [],
                        'purchases_details': [],
                        'expenses_details': []
                    }
                months[month_key]['expenses'] += expense['amount']
                months[month_key]['expenses_details'].append({
                    'date': expense['date'],
                    'description': expense['description'],
                    'amount': expense['amount']
                })
            
            grouped_balance = [
                {
                    'period': data['name'],
                    'date': data['date'],
                    'sales': data['sales'],
                    'commissions': data['commissions'],
                    'purchases': data['purchases'],
                    'expenses': data['expenses'],
                    'balance': data['sales'] - data['purchases'] - data['expenses'],
                    'sales_details': data['sales_details'],
                    'commission_details': data['commission_details'],
                    'purchases_details': data['purchases_details'],
                    'expenses_details': data['expenses_details']
                }
                for data in months.values()
            ]
            
        elif selected_range == 'last-30':
            # Show one card for the 30-day period
            period_total = {
                'sales': sum(s['total_sales'] for s in sales),
                'purchases': sum(p['total_cost'] for p in period_purchases),
                'expenses': sum(e['amount'] for e in period_expenses)
            }
            
            grouped_balance = [{
                'period': 'Últimos 30 días',
                'date': end_date,  # Use end_date for sorting
                'sales': period_total['sales'],
                'commissions': sum(s['commission'] for s in sales),
                'purchases': period_total['purchases'],
                'expenses': period_total['expenses'],
                'balance': period_total['sales'] - period_total['purchases'] - period_total['expenses'],
                'sales_details': [{
                    'date': sale['date'],
                    'username': next((u['username'] for u in users if u['user_id'] == sale['user_id']), 'Usuario desconocido'),
                    'total_sales': sale['total_sales']
                } for sale in sales],
                'commission_details': [{
                    'date': sale['date'],
                    'username': next((u['username'] for u in users if u['user_id'] == sale['user_id']), 'Usuario desconocido'),
                    'commission': sale['commission']
                } for sale in sales],
                'purchases_details': [{
                    'date': purchase['date'],
                    'total_cost': purchase['total_cost'],
                    'products': [p['name'] for p in products if p['product_id'] in [d['product_id'] for d in purchase_details if d['purchase_id'] == purchase['purchase_id']]],
                    'products_details': [
                        {
                            'name': next((p['name'] for p in products if p['product_id'] == detail['product_id']), 'Producto no encontrado'),
                            'quantity': detail['quantity'],
                            'unit_cost': detail['unit_cost']
                        }
                        for detail in purchase_details
                        if detail['purchase_id'] == purchase['purchase_id']
                    ]
                } for purchase in period_purchases],
                'expenses_details': period_expenses
            }]
        
        # Sort by date/period
        grouped_balance.sort(key=lambda x: x['date'], reverse=True)
        
        return render_template(
            'admin/view_balance.html',
            total_sales=total_sales,
            total_commissions=total_commissions,
            total_purchases=total_purchases,
            total_expenses=total_expenses,
            total_balance=total_balance,
            balance_items=grouped_balance,
            start_date=start_date,
            end_date=end_date,
            selected_range=selected_range
        )
        
    except FileNotFoundError:
        return render_template(
            'admin/view_balance.html',
            total_sales=0,
            total_commissions=0,
            total_purchases=0,
            total_expenses=0,
            total_balance=0,
            balance_items=[],
            start_date=start_date,
            end_date=end_date,
            selected_range=selected_range
        ) 