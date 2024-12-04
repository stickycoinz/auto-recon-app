"""
Auto Recon Management System
A streamlined vehicle reconditioning management system.
"""
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from auto_recon_app.extensions import db

# Initialize extensions
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Default configuration
    app.config['SECRET_KEY'] = 'dev'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auto_recon.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_SECRET_KEY'] = 'csrf-key'
    
    # Override with any custom config
    if config:
        app.config.update(config)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Enable HTTPS headers
    Talisman(app, 
             content_security_policy={
                 'default-src': "'self'",
                 'script-src': "'self' 'unsafe-inline'",
                 'style-src': "'self' 'unsafe-inline'",
             },
             force_https=False)  # Set to True in production
    
    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from auto_recon_app.auth import bp as auth_bp
    from auto_recon_app.vehicle import bp as vehicle_bp
    from auto_recon_app.workflow import bp as workflow_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(vehicle_bp)
    app.register_blueprint(workflow_bp)
    
    return app