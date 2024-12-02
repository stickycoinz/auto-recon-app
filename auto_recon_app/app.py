from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash
import pathlib
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auto_recon.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Fix upload folder path for Windows
base_dir = pathlib.Path(__file__).parent.absolute()
upload_dir = base_dir / 'static' / 'uploads'
app.config['UPLOAD_FOLDER'] = str(upload_dir)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
upload_dir.mkdir(parents=True, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Vehicle(db.Model):
    __tablename__ = 'vehicle'
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    vin = db.Column(db.String(17))
    po_number = db.Column(db.String(50))
    ro_number = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    work_orders = db.relationship('WorkOrder', backref='vehicle', lazy=True, cascade="all, delete-orphan")

class Service(db.Model):
    __tablename__ = 'service'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))

class WorkOrder(db.Model):
    __tablename__ = 'work_order'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    phase = db.Column(db.String(20), default='body_shop')
    notes = db.Column(db.Text)
    total_cost = db.Column(db.Float, default=0.0)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    completed_date = db.Column(db.DateTime)
    services = db.relationship('Service', secondary='work_order_service', backref=db.backref('work_orders', lazy=True))

work_order_service = db.Table('work_order_service',
    db.Column('work_order_id', db.Integer, db.ForeignKey('work_order.id'), primary_key=True),
    db.Column('service_id', db.Integer, db.ForeignKey('service.id'), primary_key=True)
)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    total_vehicles = Vehicle.query.count()
    total_work_orders = WorkOrder.query.count()
    completed_work_orders = WorkOrder.query.filter_by(phase='completed').count()
    
    completed_orders = WorkOrder.query.filter_by(phase='completed').all()
    total_revenue = sum(order.total_cost or 0 for order in completed_orders)
    
    # Calculate completion rate
    completion_rate = (completed_work_orders / total_work_orders * 100) if total_work_orders > 0 else 0
    
    # Calculate average service time
    completed_orders_with_dates = WorkOrder.query.filter_by(phase='completed').all()
    avg_service_time = 0
    if completed_orders_with_dates:
        total_days = sum((order.completed_date - order.created_date).days for order in completed_orders_with_dates if order.completed_date)
        avg_service_time = total_days / len(completed_orders_with_dates)
    
    # Get service statistics
    service_counts = {}
    service_revenue = {}
    for order in completed_orders:
        for service in order.services:
            service_counts[service.name] = service_counts.get(service.name, 0) + 1
            service_revenue[service.name] = service_revenue.get(service.name, 0) + service.price
    
    # Get monthly revenue data
    monthly_revenue = {}
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)
    monthly_orders = WorkOrder.query.filter(
        WorkOrder.created_date >= twelve_months_ago
    ).all()
    
    for order in monthly_orders:
        month_key = order.created_date.strftime('%Y-%m')
        monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + (order.total_cost or 0)
    
    # Sort monthly revenue by date
    monthly_revenue = dict(sorted(monthly_revenue.items()))
    
    # Get work in progress
    work_in_progress = {
        'Body Shop': WorkOrder.query.filter_by(phase='body_shop').count(),
        'Detail': WorkOrder.query.filter_by(phase='detail').count(),
        'Wheels': WorkOrder.query.filter_by(phase='wheels').count(),
        'PDR': WorkOrder.query.filter_by(phase='pdr').count(),
        'Photos': WorkOrder.query.filter_by(phase='photos').count(),
        'QC': WorkOrder.query.filter_by(phase='qc').count()
    }
    
    recent_orders = WorkOrder.query.order_by(WorkOrder.created_date.desc()).limit(5).all()
    
    return render_template('index.html',
        total_vehicles=total_vehicles,
        total_work_orders=total_work_orders,
        completed_work_orders=completed_work_orders,
        total_revenue=total_revenue,
        completion_rate=completion_rate,
        avg_service_time=avg_service_time,
        service_counts=service_counts,
        service_revenue=service_revenue,
        monthly_revenue=monthly_revenue,
        work_in_progress=work_in_progress,
        recent_orders=recent_orders
    )

@app.route('/workflow')
@login_required
def workflow_board():
    search_vin = request.args.get('vin', '').strip()
    days_old = request.args.get('days_old', type=int)
    current_phase = request.args.get('current_phase', '').strip()
    
    query = WorkOrder.query.join(Vehicle)
    
    if search_vin:
        query = query.filter(Vehicle.vin.ilike(f'%{search_vin}%'))
    
    if days_old is not None and days_old > 0:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        query = query.filter(WorkOrder.created_date >= cutoff_date)
    
    query = query.filter(WorkOrder.phase != 'completed')
    work_orders = query.order_by(WorkOrder.created_date.desc()).all()
    
    phases = {
        'body_shop': {'name': 'Body Shop', 'orders': []},
        'detail': {'name': 'Detail', 'orders': []},
        'wheels': {'name': 'Wheels', 'orders': []},
        'pdr': {'name': 'PDR', 'orders': []},
        'photos': {'name': 'Photos', 'orders': []},
        'qc': {'name': 'Quality Control', 'orders': []}
    }
    
    if current_phase and current_phase in phases:
        filtered_orders = [order for order in work_orders if order.phase == current_phase]
        phases[current_phase]['orders'] = filtered_orders
    else:
        for order in work_orders:
            if order.phase in phases:
                phases[order.phase]['orders'].append(order)
    
    total_orders = len(work_orders)
    avg_age = 0
    if total_orders > 0:
        total_age = sum((datetime.utcnow() - order.created_date).days for order in work_orders)
        avg_age = total_age / total_orders
    
    return render_template('workflow_board.html',
                         phases=phases,
                         total_orders=total_orders,
                         avg_age=avg_age,
                         search_vin=search_vin,
                         days_old=days_old,
                         current_phase=current_phase)

@app.route('/vehicles')
@login_required
def vehicles():
    vehicles = Vehicle.query.all()
    return render_template('vehicles.html', vehicles=vehicles)

@app.route('/vehicles/new', methods=['GET', 'POST'])
@login_required
def new_vehicle():
    if request.method == 'POST':
        vehicle = Vehicle(
            make=request.form['make'],
            model=request.form['model'],
            year=int(request.form['year']),
            vin=request.form.get('vin'),
            po_number=request.form.get('po_number'),
            ro_number=request.form.get('ro_number'),
            created_date=datetime.strptime(request.form['created_date'], '%Y-%m-%dT%H:%M')
        )
        db.session.add(vehicle)
        
        # Create work order if services are selected
        selected_services = request.form.getlist('services')
        if selected_services:
            services = Service.query.filter(Service.id.in_(selected_services)).all()
            work_order = WorkOrder(
                vehicle=vehicle,
                phase='body_shop',
                services=services,
                total_cost=sum(service.price for service in services)
            )
            db.session.add(work_order)
        
        db.session.commit()
        flash('Vehicle created successfully!', 'success')
        return redirect(url_for('vehicles'))
    
    services = Service.query.all()
    return render_template('new_vehicle.html', services=services, current_time=datetime.utcnow())

@app.route('/vehicles/<int:vehicle_id>')
@login_required
def view_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    services = Service.query.all()
    return render_template('view_vehicle.html', vehicle=vehicle, services=services)

@app.route('/vehicles/<int:vehicle_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if request.method == 'POST':
        vehicle.make = request.form.get('make')
        vehicle.model = request.form.get('model')
        vehicle.year = int(request.form.get('year'))
        vehicle.vin = request.form.get('vin')
        vehicle.po_number = request.form.get('po_number')
        vehicle.ro_number = request.form.get('ro_number')
        vehicle.created_date = datetime.strptime(request.form.get('created_date'), '%Y-%m-%dT%H:%M')
        
        db.session.commit()
        flash('Vehicle updated successfully!', 'success')
        return redirect(url_for('vehicles'))
    
    return render_template('edit_vehicle.html', vehicle=vehicle)

@app.route('/vehicles/delete/<int:vehicle_id>', methods=['POST'])
@login_required
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    flash('Vehicle and associated work orders deleted successfully!', 'success')
    return redirect(url_for('vehicles'))

@app.route('/vehicles/<int:vehicle_id>/work_orders/new', methods=['POST'])
@login_required
def create_work_order(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    selected_services = request.form.getlist('services')
    services = Service.query.filter(Service.id.in_(selected_services)).all()
    
    if not services:
        flash('Please select at least one service', 'danger')
        return redirect(url_for('view_vehicle', vehicle_id=vehicle_id))
    
    work_order = WorkOrder(
        vehicle_id=vehicle_id,
        phase='body_shop',
        notes=request.form.get('notes'),
        services=services,
        total_cost=sum(service.price for service in services)
    )
    
    db.session.add(work_order)
    db.session.commit()
    
    flash('Work order created successfully!', 'success')
    return redirect(url_for('view_vehicle', vehicle_id=vehicle_id))

@app.route('/work_orders/<int:work_order_id>/update_phase', methods=['POST'])
@login_required
def update_work_order_phase(work_order_id):
    work_order = WorkOrder.query.get_or_404(work_order_id)
    new_phase = request.form.get('phase')
    
    if new_phase in ['body_shop', 'detail', 'wheels', 'pdr', 'photos', 'qc', 'completed']:
        work_order.phase = new_phase
        if new_phase == 'completed':
            work_order.completed_date = datetime.utcnow()
        db.session.commit()
        flash('Work order phase updated successfully!', 'success')
    
    return redirect(url_for('workflow_board'))

@app.route('/work_orders/<int:work_order_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_work_order(work_order_id):
    work_order = WorkOrder.query.get_or_404(work_order_id)
    if request.method == 'POST':
        work_order.notes = request.form.get('notes')
        
        # Update services
        selected_services = request.form.getlist('services')
        services = Service.query.filter(Service.id.in_(selected_services)).all()
        work_order.services = services
        work_order.total_cost = sum(service.price for service in services)
        
        db.session.commit()
        flash('Work order updated successfully!', 'success')
        return redirect(url_for('view_vehicle', vehicle_id=work_order.vehicle_id))
    
    services = Service.query.all()
    return render_template('edit_work_order.html', work_order=work_order, services=services)

@app.template_filter('service_names')
def service_names(services):
    """Convert a list of service objects to a list of service names."""
    return [service.name for service in services]

@app.route('/daily_report')
@login_required
def daily_report():
    # Get completed work orders
    completed_orders = WorkOrder.query.filter_by(phase='completed').order_by(WorkOrder.completed_date.desc()).all()
    
    # Get in-progress work orders
    in_progress_orders = WorkOrder.query.filter(WorkOrder.phase != 'completed').order_by(WorkOrder.created_date.desc()).all()
    
    return render_template('daily_report.html', 
                         completed_orders=completed_orders,
                         in_progress_orders=in_progress_orders)

@app.route('/work_orders')
@login_required
def work_orders():
    work_orders = WorkOrder.query.order_by(WorkOrder.created_date.desc()).all()
    return render_template('work_orders.html', work_orders=work_orders)

@app.route('/work_orders/<int:work_order_id>')
@login_required
def view_work_order(work_order_id):
    work_order = WorkOrder.query.get_or_404(work_order_id)
    return render_template('view_work_order.html', work_order=work_order)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.context_processor
def utility_processor():
    return {
        'get_current_time': lambda: datetime.utcnow()
    }

if __name__ == '__main__':
    app.run(debug=True)
    