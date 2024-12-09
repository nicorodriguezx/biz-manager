from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import date, datetime
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from .models import log_transaction, get_daily_transactions, read_json, write_json, User
from .utils.utils import calculate_daily_summary, get_active_products, get_active_products_list

main = Blueprint('main', __name__)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    flash('Por favor inicie sesión para acceder a esta página.', 'danger')
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.authenticate(username, password)
        
        if user:
            login_user(user, remember=True)
            # Redirect based on user role
            if user.is_admin:
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('main.user_dashboard'))
        else:
            flash('Usuario o contraseña inválidos.', 'danger')
    
    # If user is already logged in, redirect appropriately
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('main.user_dashboard'))
    
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada exitosamente.', 'success')
    return redirect(url_for('main.login'))

@main.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('main.user_dashboard'))
    return redirect(url_for('main.login'))

@main.route('/dashboard')
@login_required
def user_dashboard():
    transaction_date = date.today().isoformat()
    date_without_time = transaction_date.split('T')[0]
    
    # Check if there's already a summary for today
    try:
        sales_summaries = read_json('sales_summaries.json')
        today_summary = next(
            (s for s in sales_summaries if s['date'] == date_without_time and s['user_id'] == current_user.user_id), 
            None
        )
    except FileNotFoundError:
        today_summary = None

    if today_summary:
        return render_template('dashboard.html', today_summary=today_summary)
    
    active_products = get_active_products(current_user.user_id, transaction_date)
    return render_template('dashboard.html', 
                         today_summary=None,
                         active_products=active_products)

@main.route('/log/extract', methods=['GET', 'POST'])
@login_required
def log_extract():
    if request.method == 'POST':
        details = request.json.get('details')
        if not details:
            return {"error": "Entrada inválida"}, 400

        log_transaction(current_user.user_id, "extract", details)
        return {"message": "Extracción registrada exitosamente"}

    products = read_json('products.json')
    return render_template('log_extract.html', products=products)

@main.route('/log/return', methods=['GET', 'POST'])
@login_required
def log_return():
    if request.method == 'POST':
        details = request.json.get('details', [])
        finish_day = request.json.get('finishDay', False)
        
        if details:
            # Validate return quantities
            transaction_date = date.today().isoformat()
            summary = calculate_daily_summary(current_user.user_id, transaction_date)
            available_quantities = summary['sold_units']

            for detail in details:
                product_id = detail['product_id']
                return_quantity = detail['quantity']
                available = available_quantities.get(product_id, 0)
                
                if return_quantity > available:
                    return {
                        "error": f"Error: Intentando devolver {return_quantity} unidades del producto {product_id}, pero solo tiene {available} disponibles."
                    }, 400

            log_transaction(current_user.user_id, "return", details)

        if finish_day:
            session['can_access_summary'] = True
            return {
                "summary": True,
                "redirect_url": url_for('main.day_summary')
            }
            
        return {"message": "Devolución registrada exitosamente"}

    # For GET request
    transaction_date = date.today().isoformat()
    active_products = get_active_products_list(current_user.user_id, transaction_date)
    return render_template('log_return.html', products=active_products)

@main.route('/day-summary')
@login_required
def day_summary():
    # Check if access is allowed
    if not session.get('can_access_summary'):
        flash('Acceso no autorizado al resumen del día.', 'danger')
        return redirect(url_for('main.user_dashboard'))
    
    transaction_date = date.today().isoformat()
    products = read_json('products.json')
    products_dict = {p['product_id']: p for p in products}
    summary = calculate_daily_summary(current_user.user_id, transaction_date)
    
    # Keep the session flag for page reloads
    session['can_access_summary'] = True
    
    return render_template(
        'day_summary.html',
        sold_units=summary['sold_units'],
        total_sales=summary['total_sales'],
        commission=summary['commission'],
        commission_rate=summary['commission_rate'],
        products=products_dict,
    )

@main.route('/return-payment', methods=['POST'])
@login_required
def return_payment():
    try:
        session.pop('can_access_summary', None)
        
        data = request.json
        efectivo = float(data.get('efectivo', 0))
        mercadopago = float(data.get('mercadopago', 0))

        transaction_date = date.today().isoformat()
        current_time = datetime.now().isoformat()
        summary = calculate_daily_summary(current_user.user_id, transaction_date)
        total_return = summary['total_sales'] - summary['commission']

        if abs((efectivo + mercadopago) - total_return) > 0.01:
            return {
                "success": False,
                "error": "El monto total debe coincidir con el monto a devolver"
            }

        try:
            sales_summaries = read_json('sales_summaries.json')
        except FileNotFoundError:
            sales_summaries = []

        products = read_json('products.json')
        products_dict = {p['product_id']: p for p in products}
        
        new_summary = {
            "summary_id": len(sales_summaries) + 1,
            "user_id": current_user.user_id,
            "date": transaction_date.split('T')[0],
            "timestamp": current_time,
            "products": [
                {
                    "product_id": pid,
                    "sold_units": quantity,
                    "unit_price": products_dict[pid]['price'],
                    "total": quantity * products_dict[pid]['price']
                }
                for pid, quantity in summary['sold_units'].items()
                if quantity > 0
            ],
            "total_sales": summary['total_sales'],
            "commission": summary['commission'],
            "return_due": total_return,
            "payment_details": {
                "efectivo": efectivo,
                "mercadopago": mercadopago
            }
        }

        sales_summaries.append(new_summary)
        write_json('sales_summaries.json', sales_summaries)
        
        return {
            "success": True,
            "redirect_url": url_for('main.user_dashboard')
        }

    except Exception as e:
        print(f"Error in return_payment: {str(e)}")
        return {
            "success": False,
            "error": "Error al procesar el pago"
        }

@main.route('/cancel-return', methods=['POST'])
@login_required
def cancel_return():
    try:
        # Get today's transactions
        transaction_date = date.today().isoformat()
        transactions = read_json('transactions.json')
        
        # Find and remove the last return transaction for today
        for i in range(len(transactions) - 1, -1, -1):
            transaction = transactions[i]
            if (transaction['user_id'] == current_user.user_id and 
                transaction['type'] == 'return' and 
                transaction['timestamp'].startswith(transaction_date)):
                del transactions[i]
                write_json('transactions.json', transactions)
                break
        
        return {
            "success": True,
            "redirect_url": url_for('main.log_return')
        }
    except Exception as e:
        print(f"Error in cancel_return: {str(e)}")
        return {"success": False, "error": "Error al cancelar la devolución"}
