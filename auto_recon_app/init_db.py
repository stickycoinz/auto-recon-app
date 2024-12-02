from app import db, app, User, Service, generate_password_hash
import os

def init_db():
    # Get the database file path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_recon.db')
    
    # Remove the database file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")

    with app.app_context():
        print("Creating database tables...")
        db.drop_all()  # Make sure all tables are dropped
        db.create_all()  # Create all tables fresh

        print("Adding default admin user...")
        admin = User(
            username='admin',
            password=generate_password_hash('admin')
        )
        db.session.add(admin)

        print("Adding default services...")
        services = [
            {'name': 'PDR', 'price': 85.00, 'category': 'Repair'},
            {'name': 'Detail', 'price': 125.00, 'category': 'Detailing'},
            {'name': 'Photo Package', 'price': 26.00, 'category': 'Photography'},
            {'name': 'Paint Front Bumper', 'price': 165.00, 'category': 'Paint'},
            {'name': 'Paint Rear Bumper', 'price': 165.00, 'category': 'Paint'},
            {'name': 'Paint Door - Left', 'price': 250.00, 'category': 'Paint'},
            {'name': 'Paint Door - Right', 'price': 250.00, 'category': 'Paint'},
            {'name': 'Paint Quarter Panel - Left', 'price': 250.00, 'category': 'Paint'},
            {'name': 'Paint Quarter Panel - Right', 'price': 250.00, 'category': 'Paint'},
            {'name': 'Paint Fender - Left', 'price': 250.00, 'category': 'Paint'},
            {'name': 'Paint Fender - Right', 'price': 250.00, 'category': 'Paint'}
        ]

        for service_data in services:
            service = Service(**service_data)
            db.session.add(service)

        try:
            print("Committing changes...")
            db.session.commit()
            print("Database initialized successfully!")
        except Exception as e:
            print(f"Error during commit: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    init_db() 