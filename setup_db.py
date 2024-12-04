from auto_recon_app.app import app, db
from auto_recon_app.models import User, Service, Vehicle, Dealership, PhaseHistory
from datetime import datetime
from werkzeug.security import generate_password_hash

def setup_database():
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            print("Dropped all tables")
            
            # Create all tables
            db.create_all()
            print("Created all tables")
            
            # Create default dealership first
            dealership = Dealership(
                name='Main Dealership',
                location='123 Main St',
                email_primary='contact@maindealership.com'
            )
            db.session.add(dealership)
            db.session.commit()  # Commit to ensure dealership has an ID
            print("Added default dealership")
            
            # Create default admin user and assign to dealership
            admin = User(
                username='admin',
                email='admin@example.com',
                role='corporate',
                is_active=True,
                created_date=datetime.utcnow()
            )
            admin.set_password('admin')  # Set password explicitly
            admin.dealerships.append(dealership)
            db.session.add(admin)
            db.session.commit()  # Commit to ensure admin has an ID
            print("Added admin user (username: admin, password: admin)")
            
            # Create default services with correct prices
            services = [
                Service(
                    name='PDR',
                    base_price=85.00,
                    category='PDR',
                    is_active=True,
                    tags='dent,repair,pdr',
                    description='Paintless Dent Repair'
                ),
                Service(
                    name='Detail',
                    base_price=125.00,
                    category='Detail',
                    is_active=True,
                    tags='clean,detail,interior,exterior',
                    description='Full vehicle detailing service'
                ),
                Service(
                    name='Photo Package',
                    base_price=26.00,
                    category='Photos',
                    is_active=True,
                    tags='photo,pictures,documentation',
                    description='Professional photo package'
                ),
                Service(
                    name='Paint Front Bumper',
                    base_price=165.00,
                    category='Paint',
                    is_active=True,
                    tags='paint,bumper,front',
                    description='Paint front bumper'
                ),
                Service(
                    name='Paint Rear Bumper',
                    base_price=165.00,
                    category='Paint',
                    is_active=True,
                    tags='paint,bumper,rear',
                    description='Paint rear bumper'
                ),
                Service(
                    name='Paint Door - Left',
                    base_price=250.00,
                    category='Paint',
                    is_active=True,
                    tags='paint,door,left',
                    description='Paint left door'
                ),
                Service(
                    name='Paint Door - Right',
                    base_price=250.00,
                    category='Paint',
                    is_active=True,
                    tags='paint,door,right',
                    description='Paint right door'
                ),
                Service(
                    name='Paint Quarter Panel - Left',
                    base_price=250.00,
                    category='Paint',
                    is_active=True,
                    tags='paint,quarter,panel,left',
                    description='Paint left quarter panel'
                ),
                Service(
                    name='Paint Quarter Panel - Right',
                    base_price=250.00,
                    category='Paint',
                    is_active=True,
                    tags='paint,quarter,panel,right',
                    description='Paint right quarter panel'
                ),
                Service(
                    name='Paint Fender - Left',
                    base_price=250.00,
                    category='Paint',
                    is_active=True,
                    tags='paint,fender,left',
                    description='Paint left fender'
                ),
                Service(
                    name='Paint Fender - Right',
                    base_price=250.00,
                    category='Paint',
                    is_active=True,
                    tags='paint,fender,right',
                    description='Paint right fender'
                ),
                Service(
                    name='Wheel Repair',
                    base_price=50.00,
                    category='Wheels',
                    is_active=True,
                    is_quantity_based=True,
                    max_quantity=4,
                    tags='wheel,repair,rim',
                    description='Wheel repair service (per wheel)'
                ),
                Service(
                    name='Touch Up',
                    base_price=75.00,
                    category='Touch Up',
                    is_active=True,
                    tags='touch,up,paint,minor',
                    description='Minor paint touch up service'
                ),
                Service(
                    name='Quality Control',
                    base_price=0.00,
                    category='QC',
                    is_active=True,
                    tags='qc,quality,control,inspection',
                    description='Final quality control inspection'
                )
            ]
            
            # Add services and commit to get IDs
            for service in services:
                db.session.add(service)
            db.session.commit()
            print("Added default services")
            
            # Add services to dealership and set prices
            for service in services:
                # First add service to dealership's services
                dealership.services.append(service)
                db.session.flush()
                
                # Then explicitly set the price
                dealership.set_service_price(service.id, service.base_price)
            
            # Commit dealership services and prices
            db.session.commit()
            print("Added services to dealership with prices")
            
            print("\nDatabase setup completed successfully!")
            
        except Exception as e:
            print(f"\nError during database setup: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    setup_database() 