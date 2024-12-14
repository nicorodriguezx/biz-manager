"""
Utility functions for the application.

This module provides helper functions for:
- Calculating daily sales summaries and commissions
- Managing active products and their quantities
- Text processing utilities
"""

from ..models import get_daily_transactions, read_json, User

def calculate_daily_summary(user_id, transaction_date):
    """Calculate sold units, gross revenue, and returns."""
    transactions = get_daily_transactions(user_id, transaction_date)
    products = read_json('products.json')
    product_prices = {p['product_id']: p['price'] for p in products}

    extracted = {}
    returned = {}

    for t in transactions:
        for detail in t['details']:
            product_id = detail['product_id']
            quantity = detail['quantity']
            if t['type'] == 'extract':
                extracted[product_id] = extracted.get(product_id, 0) + quantity
            elif t['type'] == 'return':
                returned[product_id] = returned.get(product_id, 0) + quantity

    sold_units = {
        pid: extracted.get(pid, 0) - returned.get(pid, 0)
        for pid in set(extracted) | set(returned)
    }
    total_sales = sum(sold_units[pid] * product_prices[pid] for pid in sold_units)
    
    # Get user's commission rate
    user = User.get_user(user_id)
    commission = total_sales * user.commission_rate

    return {
        "sold_units": sold_units, 
        "total_sales": total_sales, 
        "commission": commission,
        "commission_rate": user.commission_rate
    }

def get_active_products(user_id, transaction_date):
    """Get products with positive quantities (extracted - returned > 0)."""
    summary = calculate_daily_summary(user_id, transaction_date)
    
    # Get products with positive quantities
    active_quantities = {
        pid: qty for pid, qty in summary['sold_units'].items() 
        if qty > 0
    }
    
    if not active_quantities:
        return None
    
    # Get product details
    products = read_json('products.json')
    products_dict = {p['product_id']: p for p in products}
    
    return {
        product_id: {
            'name': products_dict[product_id]['name'],
            'price': products_dict[product_id]['price'],
            'quantity': quantity
        }
        for product_id, quantity in active_quantities.items()
    }

def get_active_products_list(user_id, transaction_date):
    """Same as get_active_products but returns a list format for templates that need it."""
    active_products = get_active_products(user_id, transaction_date)
    
    if not active_products:
        return []
        
    # Create and sort the list alphabetically by name
    products_list = [
        {
            'product_id': product_id,
            'name': product['name'],
            'price': product['price'],
            'available': product['quantity']
        }
        for product_id, product in active_products.items()
    ]
    products_list.sort(key=lambda x: x['name'])
    return products_list

def slugify(text):
    """Convert text to URL-friendly slug"""
    return text.lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
