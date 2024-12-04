from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from auto_recon_app.extensions import db

# Association tables
vehicle_services = db.Table('vehicle_services',
    db.Column('vehicle_id', db.Integer, db.ForeignKey('vehicle.id')),
    db.Column('service_id', db.Integer, db.ForeignKey('service.id')),
    db.Column('quantity', db.Integer, default=1),
    db.Column('price_at_time', db.Float),  # Price when service was added
    extend_existing=True
)

dealership_services = db.Table('dealership_services',
    db.Column('dealership_id', db.Integer, db.ForeignKey('dealership.id')),
    db.Column('service_id', db.Integer, db.ForeignKey('service.id')),
    db.Column('custom_price', db.Float),  # Dealership-specific price
    db.Column('is_active', db.Boolean, default=True),
    extend_existing=True
)

user_dealerships = db.Table('user_dealerships',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('dealership_id', db.Integer, db.ForeignKey('dealership.id')),
    extend_existing=True
)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(20), default='ground_manager')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    dealerships = db.relationship('Dealership', secondary=user_dealerships, back_populates='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Dealership(db.Model):
    __tablename__ = 'dealership'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    email_primary = db.Column(db.String(120))
    email_service = db.Column(db.String(120))
    email_parts = db.Column(db.String(120))
    email_billing = db.Column(db.String(120))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('User', secondary=user_dealerships, back_populates='dealerships')
    vehicles = db.relationship('Vehicle', back_populates='dealership')
    services = db.relationship('Service', secondary=dealership_services, back_populates='dealerships')

    def set_service_price(self, service_id, price):
        """Set a custom price for a service at this dealership"""
        stmt = dealership_services.update().where(
            dealership_services.c.dealership_id == self.id,
            dealership_services.c.service_id == service_id
        ).values(custom_price=price)
        result = db.session.execute(stmt)
        if result.rowcount == 0:
            # If no existing record, insert new one
            stmt = dealership_services.insert().values(
                dealership_id=self.id,
                service_id=service_id,
                custom_price=price,
                is_active=True
            )
            db.session.execute(stmt)
        db.session.flush()

    def __repr__(self):
        return f'<Dealership {self.name}>'

class Service(db.Model):
    __tablename__ = 'service'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    base_price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    is_quantity_based = db.Column(db.Boolean, default=False)
    max_quantity = db.Column(db.Integer, default=1)
    tags = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    vehicles = db.relationship('Vehicle', secondary=vehicle_services, back_populates='services')
    dealerships = db.relationship('Dealership', secondary=dealership_services, back_populates='services')

    def get_price_for_dealership(self, dealership_id):
        """Get the price for this service at a specific dealership"""
        result = db.session.execute(
            dealership_services.select()
            .where(
                dealership_services.c.dealership_id == dealership_id,
                dealership_services.c.service_id == self.id
            )
        ).first()
        return result.custom_price if result else self.base_price

    def __repr__(self):
        return f'<Service {self.name}>'

class Vehicle(db.Model):
    __tablename__ = 'vehicle'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    vin = db.Column(db.String(17))
    stock_number = db.Column(db.String(50))
    po_number = db.Column(db.String(50))
    ro_number = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    completed_date = db.Column(db.DateTime)
    phase_start_date = db.Column(db.DateTime, default=datetime.utcnow)
    current_phase = db.Column(db.String(20), default='received')
    notes = db.Column(db.Text)
    total_cost = db.Column(db.Float, default=0.0)
    dealership_id = db.Column(db.Integer, db.ForeignKey('dealership.id'))
    dealership = db.relationship('Dealership', back_populates='vehicles')
    services = db.relationship('Service', secondary=vehicle_services, back_populates='vehicles')
    phase_history = db.relationship('PhaseHistory', back_populates='vehicle', lazy=True, cascade='all, delete-orphan')

    def add_service(self, service, quantity=1):
        """Add a service with specified quantity and store current price"""
        if service.is_quantity_based and quantity > service.max_quantity:
            quantity = service.max_quantity
        
        price = service.get_price_for_dealership(self.dealership_id)
        total_price = price * quantity
        
        # Add service with quantity and current price
        stmt = vehicle_services.insert().values(
            vehicle_id=self.id,
            service_id=service.id,
            quantity=quantity,
            price_at_time=price
        )
        db.session.execute(stmt)
        
        # Update total cost
        self.total_cost += total_price
        db.session.flush()

    def update_phase(self, new_phase, notes=None):
        """Update vehicle phase and record in history"""
        self.current_phase = new_phase
        self.phase_start_date = datetime.utcnow()
        
        # Record phase change in history
        history_entry = PhaseHistory(
            vehicle=self,
            phase=new_phase,
            notes=notes
        )
        db.session.add(history_entry)
        db.session.flush()

    def __repr__(self):
        return f'<Vehicle {self.make} {self.model} ({self.year})>'

class PhaseHistory(db.Model):
    __tablename__ = 'phase_history'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    phase = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text)
    
    # Relationship to Vehicle
    vehicle = db.relationship('Vehicle', back_populates='phase_history')

    def __repr__(self):
        return f'<PhaseHistory {self.vehicle_id} - {self.phase}>' 