from auto_recon_app.app import app, db, User
from datetime import datetime

def create_admin():
    with app.app_context():
        try:
            # Check if admin user exists
            admin = User.query.filter_by(username='admin').first()
            if admin:
                print("Admin user already exists")
                return
            
            # Create new admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                role='corporate',
                is_active=True,
                created_date=datetime.utcnow()
            )
            admin.set_password('admin')  # Set password to 'admin'
            
            db.session.add(admin)
            db.session.commit()
            print("Successfully created admin user (username: admin, password: admin)")
        except Exception as e:
            print(f"Error creating admin user: {e}")
            db.session.rollback()

if __name__ == '__main__':
    create_admin() 