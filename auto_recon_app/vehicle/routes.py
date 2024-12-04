"""Vehicle management routes."""
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from auto_recon_app.vehicle import bp
from auto_recon_app.models import Vehicle, Service, Dealership, PhaseHistory
from auto_recon_app.extensions import db

@bp.route('/')
@login_required
def list_vehicles():
    """List all vehicles."""
    vehicles = Vehicle.query.all()
    return render_template('vehicle/list.html', vehicles=vehicles)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_vehicle():
    """Create a new vehicle."""
    if request.method == 'POST':
        try:
            # Get the dealership
            dealership_id = request.form.get('dealership_id')
            if not dealership_id:
                flash('Please select a dealership', 'danger')
                return redirect(url_for('vehicle.new_vehicle'))
            
            dealership = Dealership.query.get(dealership_id)
            if not dealership:
                flash('Invalid dealership selected', 'danger')
                return redirect(url_for('vehicle.new_vehicle'))

            # Create the vehicle
            vehicle = Vehicle(
                make=request.form['make'],
                model=request.form['model'],
                year=int(request.form['year']),
                vin=request.form.get('vin'),
                stock_number=request.form.get('stock_number'),
                po_number=request.form.get('po_number'),
                ro_number=request.form.get('ro_number'),
                created_date=datetime.strptime(request.form['created_date'], '%Y-%m-%dT%H:%M'),
                notes=request.form.get('notes'),
                dealership_id=dealership.id,
                current_phase='received'
            )
            db.session.add(vehicle)
            db.session.flush()  # Get vehicle ID for relationships
            
            # Handle selected services
            selected_services = request.form.getlist('services')
            if selected_services:
                for service_id in selected_services:
                    service = Service.query.get(service_id)
                    if service:
                        # Get quantity if it's a quantity-based service
                        quantity = 1
                        if service.is_quantity_based:
                            quantity = int(request.form.get(f'quantity_{service_id}', 1))
                            if quantity > service.max_quantity:
                                quantity = service.max_quantity
                        
                        # Add service to vehicle with quantity and dealership-specific price
                        vehicle.add_service(service, quantity)

            # Create initial phase history entry
            phase_history = PhaseHistory(
                vehicle=vehicle,
                phase='received',
                notes=request.form.get('notes')
            )
            db.session.add(phase_history)
            
            db.session.commit()
            flash('Vehicle added successfully with selected services!', 'success')
            return redirect(url_for('workflow.board'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding vehicle: {str(e)}', 'danger')
            return redirect(url_for('vehicle.new_vehicle'))
    
    # GET request - show the form
    services = Service.query.filter_by(is_active=True).order_by(Service.category, Service.name).all()
    dealerships = Dealership.query.order_by(Dealership.name).all()
    return render_template('vehicle/new.html', 
                         services=services, 
                         dealerships=dealerships,
                         current_datetime=datetime.now().strftime('%Y-%m-%dT%H:%M'),
                         current_year=datetime.now().year)

@bp.route('/<int:vehicle_id>')
@login_required
def view_vehicle(vehicle_id):
    """View vehicle details."""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    return render_template('vehicle/view.html', vehicle=vehicle)

@bp.route('/<int:vehicle_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_vehicle(vehicle_id):
    """Edit vehicle details."""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if request.method == 'POST':
        vehicle.make = request.form.get('make')
        vehicle.model = request.form.get('model')
        vehicle.year = int(request.form.get('year'))
        vehicle.vin = request.form.get('vin')
        vehicle.stock_number = request.form.get('stock_number')
        vehicle.po_number = request.form.get('po_number')
        vehicle.ro_number = request.form.get('ro_number')
        vehicle.notes = request.form.get('notes')
        
        db.session.commit()
        flash('Vehicle updated successfully!', 'success')
        return redirect(url_for('vehicle.view_vehicle', vehicle_id=vehicle.id))
    
    return render_template('vehicle/edit.html', vehicle=vehicle)

@bp.route('/<int:vehicle_id>/delete', methods=['POST'])
@login_required
def delete_vehicle(vehicle_id):
    """Delete a vehicle."""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    flash('Vehicle deleted successfully!', 'success')
    return redirect(url_for('vehicle.list_vehicles'))

@bp.route('/api/services/prices')
@login_required
def get_service_prices():
    """Get service prices for a dealership."""
    dealership_id = request.args.get('dealership_id', type=int)
    if not dealership_id:
        return jsonify({'error': 'Dealership ID is required'}), 400
    
    try:
        services = Service.query.filter_by(is_active=True).all()
        prices = {}
        for service in services:
            prices[str(service.id)] = service.get_price_for_dealership(dealership_id)
        return jsonify(prices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 