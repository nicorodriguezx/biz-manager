from flask import Flask
from flask_login import LoginManager
from .routes import main, login_manager
from datetime import timedelta

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
    
    # Configure Flask-Login for persistent sessions
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)  # Cookie will last 30 days
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
    app.config['SESSION_PERMANENT'] = True
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    
    # Register blueprints
    app.register_blueprint(main)
    
    return app
