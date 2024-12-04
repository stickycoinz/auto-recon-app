"""Authentication routes."""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from auto_recon_app.auth import bp
from auto_recon_app.models import User
from auto_recon_app.extensions import db

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('workflow.board'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('workflow.board'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register a new user (admin only)."""
    if not current_user.role == 'corporate':
        flash('Only corporate users can register new users', 'danger')
        return redirect(url_for('workflow.board'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        role = request.form.get('role', 'ground_manager')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('auth.register'))
        
        user = User(
            username=username,
            email=email,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('User registered successfully', 'success')
        return redirect(url_for('auth.users'))
    
    return render_template('auth/register.html')

@bp.route('/users')
@login_required
def users():
    """List all users (admin only)."""
    if not current_user.role == 'corporate':
        flash('Access denied', 'danger')
        return redirect(url_for('workflow.board'))
    
    users = User.query.all()
    return render_template('auth/users.html', users=users) 