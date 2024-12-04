"""Update schema for vehicle services and pricing

This migration adds quantity and price tracking to vehicle services,
and adds dealership-specific pricing capabilities.
"""

from flask import current_app
from sqlalchemy import create_engine, text, inspect
from auto_recon_app.app import app

def table_exists(conn, table_name):
    try:
        conn.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
        return True
    except:
        return False

def drop_table_if_exists(conn, table_name):
    try:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
    except:
        pass

def upgrade():
    # Create engine using app's database URI
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    
    with engine.connect() as conn:
        # Drop temporary tables if they exist from failed migrations
        drop_table_if_exists(conn, 'vehicle_services_new')
        drop_table_if_exists(conn, 'vehicle_services_old')
        
        # Create vehicle_services_new table
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS vehicle_services_new (
                vehicle_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                price_at_time FLOAT,
                PRIMARY KEY (vehicle_id, service_id),
                FOREIGN KEY(vehicle_id) REFERENCES vehicle (id),
                FOREIGN KEY(service_id) REFERENCES service (id)
            )
        '''))
        
        # Copy data if old table exists
        if table_exists(conn, 'vehicle_services'):
            try:
                conn.execute(text('''
                    INSERT INTO vehicle_services_new (vehicle_id, service_id, quantity, price_at_time)
                    SELECT vs.vehicle_id, vs.service_id, 1, s.base_price
                    FROM vehicle_services vs
                    JOIN service s ON s.id = vs.service_id
                '''))
            except:
                pass
            
            # Drop old table
            drop_table_if_exists(conn, 'vehicle_services')
        
        # Rename new table
        conn.execute(text('ALTER TABLE vehicle_services_new RENAME TO vehicle_services'))
        
        # Create dealership_services table if it doesn't exist
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS dealership_services (
                dealership_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                custom_price FLOAT,
                is_active BOOLEAN DEFAULT 1,
                PRIMARY KEY (dealership_id, service_id),
                FOREIGN KEY(dealership_id) REFERENCES dealership (id),
                FOREIGN KEY(service_id) REFERENCES service (id)
            )
        '''))
        
        # Initialize dealership services with base prices if empty
        result = conn.execute(text("SELECT COUNT(*) FROM dealership_services")).scalar()
        if result == 0:
            try:
                conn.execute(text('''
                    INSERT INTO dealership_services (dealership_id, service_id, custom_price, is_active)
                    SELECT d.id, s.id, s.base_price, 1
                    FROM dealership d
                    CROSS JOIN service s
                    WHERE s.is_active = 1
                '''))
            except:
                pass
        
        conn.commit()

def downgrade():
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    
    with engine.connect() as conn:
        # Drop temporary tables if they exist
        drop_table_if_exists(conn, 'vehicle_services_old')
        
        # Revert vehicle_services table
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS vehicle_services_old (
                vehicle_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                PRIMARY KEY (vehicle_id, service_id),
                FOREIGN KEY(vehicle_id) REFERENCES vehicle (id),
                FOREIGN KEY(service_id) REFERENCES service (id)
            )
        '''))
        
        # Copy existing relationships without quantity and price
        try:
            conn.execute(text('''
                INSERT INTO vehicle_services_old (vehicle_id, service_id)
                SELECT DISTINCT vehicle_id, service_id FROM vehicle_services
            '''))
        except:
            pass
        
        # Drop new tables and rename old one back
        drop_table_if_exists(conn, 'vehicle_services')
        drop_table_if_exists(conn, 'dealership_services')
        conn.execute(text('ALTER TABLE vehicle_services_old RENAME TO vehicle_services'))
        
        conn.commit() 