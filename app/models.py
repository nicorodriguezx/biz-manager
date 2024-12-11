import json
import os
from datetime import datetime
from werkzeug.security import check_password_hash
from flask_login import UserMixin

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def read_json(file_name):
    with open(os.path.join(DATA_DIR, file_name), 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(file_name, data):
    with open(os.path.join(DATA_DIR, file_name), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def log_transaction(user_id, transaction_type, details):
    """Log extracted or returned products."""
    # Load both files
    transactions = read_json('transactions.json')
    try:
        transaction_details = read_json('transaction_details.json')
    except FileNotFoundError:
        transaction_details = []

    # Create new transaction
    transaction_id = len(transactions) + 1
    new_transaction = {
        "transaction_id": transaction_id,
        "user_id": user_id,
        "type": transaction_type,
        "timestamp": datetime.now().isoformat()
    }
    
    # Create transaction details
    new_details = []
    for detail in details:
        detail_id = len(transaction_details) + len(new_details) + 1
        new_detail = {
            "detail_id": detail_id,
            "transaction_id": transaction_id,
            "product_id": detail["product_id"],
            "quantity": detail["quantity"]
        }
        new_details.append(new_detail)

    # Save both to their respective files
    transactions.append(new_transaction)
    transaction_details.extend(new_details)
    
    write_json('transactions.json', transactions)
    write_json('transaction_details.json', transaction_details)
    
    return new_transaction

def get_daily_transactions(user_id, transaction_date):
    """Get all transactions for a user on a specific date with their details."""
    transactions = read_json('transactions.json')
    try:
        transaction_details = read_json('transaction_details.json')
    except FileNotFoundError:
        transaction_details = []

    # Get all transactions for the user on the specified date
    user_transactions = [
        t for t in transactions 
        if t['user_id'] == user_id and t['timestamp'].startswith(transaction_date)
    ]
    
    # Add details to each transaction
    for transaction in user_transactions:
        transaction['details'] = [
            d for d in transaction_details 
            if d['transaction_id'] == transaction['transaction_id']
        ]
    
    return user_transactions

class User(UserMixin):
    def __init__(self, user_id, username, password_hash, role='user', commission_rate=None):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.commission_rate = commission_rate
        
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_authenticated(self):
        return True
        
    @property
    def is_active(self):
        return True
        
    @property
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return str(self.user_id)
        
    @staticmethod
    def get_user(user_id):
        users = read_json('users.json')
        user_data = next((u for u in users if u['user_id'] == int(user_id)), None)
        if user_data:
            return User(
                user_id=user_data['user_id'],
                username=user_data['username'],
                password_hash=user_data['password_hash'],
                role=user_data.get('role', 'user'),
                commission_rate=user_data.get('commission_rate')
            )
        return None
        
    @staticmethod
    def authenticate(username, password):
        users = read_json('users.json')
        user_data = next((u for u in users if u['username'] == username), None)
        if user_data and check_password_hash(user_data['password_hash'], password):
            return User(
                user_id=user_data['user_id'],
                username=user_data['username'],
                password_hash=user_data['password_hash'],
                role=user_data.get('role', 'user'),
                commission_rate=user_data.get('commission_rate')
            )
        return None
