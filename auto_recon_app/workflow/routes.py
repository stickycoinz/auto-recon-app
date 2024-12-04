"""Workflow management routes."""
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from auto_recon_app.workflow import bp
from auto_recon_app.models import Vehicle, Service
from auto_recon_app.extensions import db

@bp.route('/')
@login_required
def board():
    """Display the workflow board."""
    try:
        # Get filter parameters
        search_vin = request.args.get('vin', '').strip()
        days_old = request.args.get('days_old', type=int)
        current_phase = request.args.get('current_phase', '').strip()
        
        # Base query for vehicles
        query = Vehicle.query
        
        # Apply filters
        if search_vin:
            query = query.filter(Vehicle.vin.ilike(f'%{search_vin}%'))
        
        if days_old is not None and days_old > 0:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            query = query.filter(Vehicle.created_date >= cutoff_date)
        
        if current_phase:
            query = query.filter(Vehicle.current_phase == current_phase)
        
        # Only get non-completed vehicles
        query = query.filter(Vehicle.current_phase != 'completed')
        vehicles = query.order_by(Vehicle.created_date.desc()).all()
        
        # Initialize workflow data structure
        workflow_data = {
            'received': [],
            'body_shop': [],
            'detail': [],
            'wheels': [],
            'pdr': [],
            'photos': [],
            'qc': []
        }
        
        # Group vehicles by phase
        for vehicle in vehicles:
            if vehicle.current_phase in workflow_data:
                workflow_data[vehicle.current_phase].append({
                    'id': vehicle.id,
                    'vehicle': vehicle,
                    'created_date': vehicle.created_date,
                    'age_days': (datetime.utcnow() - vehicle.created_date).days,
                    'services': vehicle.services,
                    'notes': vehicle.notes
                })
        
        # Calculate statistics
        total_vehicles = len(vehicles)
        avg_age = 0
        if total_vehicles > 0:
            total_age = sum((datetime.utcnow() - vehicle.created_date).days for vehicle in vehicles)
            avg_age = total_age / total_vehicles
        
        # Get phase names for display
        phases = {
            'received': 'Received',
            'body_shop': 'Body Shop',
            'detail': 'Detail',
            'wheels': 'Wheels',
            'pdr': 'PDR',
            'photos': 'Photos',
            'qc': 'Quality Control'
        }
        
        return render_template('workflow/board.html',
            workflow_data=workflow_data,
            phases=phases,
            total_vehicles=total_vehicles,
            avg_age=avg_age,
            search_vin=search_vin,
            days_old=days_old,
            current_phase=current_phase
        )
    except Exception as e:
        flash('Error loading workflow board', 'danger')
        return render_template('workflow/board.html',
            workflow_data={},
            phases={},
            total_vehicles=0,
            avg_age=0,
            search_vin='',
            days_old=None,
            current_phase=''
        )

@bp.route('/vehicle/<int:vehicle_id>/update_phase', methods=['POST'])
@login_required
def update_vehicle_phase(vehicle_id):
    """Update a vehicle's phase."""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    new_phase = request.form.get('phase')
    notes = request.form.get('notes')
    
    if new_phase in ['received', 'body_shop', 'detail', 'wheels', 'pdr', 'photos', 'qc', 'completed']:
        vehicle.update_phase(new_phase, notes)
        if new_phase == 'completed':
            vehicle.completed_date = datetime.utcnow()
        db.session.commit()
        flash('Vehicle phase updated successfully!', 'success')
    else:
        flash('Invalid phase specified', 'danger')
    
    return redirect(url_for('workflow.board'))

@bp.route('/dashboard')
@login_required
def dashboard():
    """Display the workflow dashboard with metrics."""
    try:
        # Get current month and year
        now = datetime.utcnow()
        current_month = now.month
        current_year = now.year
        
        # Calculate metrics
        total_vehicles = Vehicle.query.count()
        active_vehicles = Vehicle.query.filter(Vehicle.current_phase != 'completed').count()
        
        # Calculate this month's revenue
        completed_vehicles = Vehicle.query.filter(
            Vehicle.completed_date.isnot(None),
            db.extract('year', Vehicle.completed_date) == current_year,
            db.extract('month', Vehicle.completed_date) == current_month
        ).all()
        this_month_revenue = sum(vehicle.total_cost or 0 for vehicle in completed_vehicles)
        
        # Calculate average completion time
        completed_vehicles_with_dates = Vehicle.query.filter(
            Vehicle.completed_date.isnot(None)
        ).all()
        
        avg_completion_time = 0
        if completed_vehicles_with_dates:
            total_days = sum(
                (vehicle.completed_date - vehicle.created_date).days 
                for vehicle in completed_vehicles_with_dates
            )
            avg_completion_time = total_days / len(completed_vehicles_with_dates)
        
        # Get service distribution
        service_stats = {}
        for vehicle in Vehicle.query.all():
            for service in vehicle.services:
                if service.category not in service_stats:
                    service_stats[service.category] = 0
                service_stats[service.category] += 1
        
        # Format service stats for chart
        service_labels = [cat.replace('_', ' ').title() for cat in service_stats.keys()]
        service_counts = list(service_stats.values())
        
        return render_template('workflow/dashboard.html',
            total_vehicles=total_vehicles,
            active_vehicles=active_vehicles,
            this_month_revenue=this_month_revenue,
            avg_completion_time=avg_completion_time,
            service_labels=service_labels,
            service_counts=service_counts
        )
    except Exception as e:
        flash('Error loading dashboard data', 'danger')
        return render_template('workflow/dashboard.html',
            total_vehicles=0,
            active_vehicles=0,
            this_month_revenue=0,
            avg_completion_time=0,
            service_labels=[],
            service_counts=[]
        ) 