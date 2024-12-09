from flask import Flask
from flask_login import LoginManager
from .models import User
from config import Config
from datetime import datetime
import locale
from .utils import slugify

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Set locale for Spanish weekday names
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    
    # Add date filter
    @app.template_filter('strftime')
    def _jinja2_filter_datetime(date_str, fmt=None):
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime(fmt)
    
    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_user(user_id)
    
    # Register blueprints
    from .routes import main
    app.register_blueprint(main)
    
    from .admin import admin
    app.register_blueprint(admin)
    
    @app.template_filter('format_money')
    def format_money(value):
        return f"$ {value:,}".replace(",", ".")
    
    app.jinja_env.filters['slugify'] = slugify
    
    return app
