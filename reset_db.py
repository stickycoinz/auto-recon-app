from auto_recon_app.app import app, db, User, Dealership
from datetime import datetime

def reset_database():
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            print("Dropped all tables")
            
            # Create all tables
            db.create_all()
            print("Created all tables")
            
            # Create default dealership
            dealership = Dealership(
                name='Main Dealership',
                location='123 Main St',
                email_primary='contact@maindealership.com',
                created_date=datetime.utcnow()
            )
            db.session.add(dealership)
            db.session.commit()
            print("Created default dealership")
            
            # Create admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                role='corporate',
                is_active=True,
                created_date=datetime.utcnow()
            )
            admin.set_password('admin')
            admin.dealerships.append(dealership)
            
            db.session.add(admin)
            db.session.commit()
            print("Created admin user (username: admin, password: admin)")
            
        except Exception as e:
            print(f"Error resetting database: {e}")
            db.session.rollback()

if __name__ == '__main__':
    reset_database() 