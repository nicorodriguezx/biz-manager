import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def read_json(file_name):
    with open(os.path.join(DATA_DIR, file_name), 'r') as f:
        return json.load(f)

def write_json(file_name, data):
    with open(os.path.join(DATA_DIR, file_name), 'w') as f:
        json.dump(data, f, indent=4)

def log_transaction(user_id, transaction_type, details):
    """Log extracted or returned products."""
    transactions = read_json('transactions.json')
    transaction_id = len(transactions) + 1
    new_transaction = {
        "transaction_id": transaction_id,
        "user_id": user_id,
        "type": transaction_type,
        "timestamp": datetime.now().isoformat(),
        "details": details
    }
    transactions.append(new_transaction)
    write_json('transactions.json', transactions)
    return new_transaction

def get_daily_transactions(user_id, transaction_date):
    """Get all transactions for a user on a specific date."""
    transactions = read_json('transactions.json')
    return [
        t for t in transactions 
        if t['user_id'] == user_id and t['timestamp'].startswith(transaction_date)
    ]

class User(UserMixin):
    def __init__(self, user_data):
        self.user_id = user_data['user_id']
        self.username = user_data['username']
        self.password_hash = user_data['password_hash']
        self.role = user_data['role']
        self.commission_rate = user_data.get('commission_rate', 0.10)  # Default 10% if not specified

    def get_id(self):
        return str(self.user_id)

    @staticmethod
    def get_user(user_id):
        users = read_json('users.json')
        user_data = next((u for u in users if u['user_id'] == int(user_id)), None)
        return User(user_data) if user_data else None

    @staticmethod
    def authenticate(username, password):
        users = read_json('users.json')
        user_data = next((u for u in users if u['username'] == username), None)
        if user_data and check_password_hash(user_data['password_hash'], password):
            return User(user_data)
        return None
