from auto_recon_app.app import app, db
from sqlalchemy import text

def update_schema():
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Create vehicle_services table if it doesn't exist
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS vehicle_services (
                        vehicle_id INTEGER NOT NULL,
                        service_id INTEGER NOT NULL,
                        PRIMARY KEY (vehicle_id, service_id),
                        FOREIGN KEY(vehicle_id) REFERENCES vehicle (id),
                        FOREIGN KEY(service_id) REFERENCES service (id)
                    )
                """))
                
                # Backup existing service data
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS service_backup AS
                    SELECT * FROM service
                """))
                
                # Create temporary service table with new schema
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS service_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        price FLOAT NOT NULL,
                        base_price FLOAT NOT NULL,
                        category VARCHAR(50) NOT NULL,
                        is_quantity_based BOOLEAN DEFAULT 0,
                        max_quantity INTEGER DEFAULT 1,
                        tags VARCHAR(200),
                        is_active BOOLEAN DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Copy data from old service table, preserving relationships
                conn.execute(text("""
                    INSERT INTO service_new (
                        id, name, price, base_price, category
                    )
                    SELECT 
                        id, name, base_price, base_price, 
                        COALESCE(category, 'uncategorized')
                    FROM service_backup
                """))
                
                # Backup work_order_service relationships
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS work_order_service_backup AS
                    SELECT * FROM work_order_service
                """))
                
                # Drop old service table and rename new one
                conn.execute(text("DROP TABLE IF EXISTS service"))
                conn.execute(text("ALTER TABLE service_new RENAME TO service"))
                
                # Restore work_order_service relationships
                conn.execute(text("""
                    INSERT INTO work_order_service
                    SELECT * FROM work_order_service_backup
                """))
                
                # Clean up backup tables
                conn.execute(text("DROP TABLE IF EXISTS service_backup"))
                conn.execute(text("DROP TABLE IF EXISTS work_order_service_backup"))
                
                # Update vehicle table if columns don't exist
                try:
                    conn.execute(text("SELECT completed_date FROM vehicle LIMIT 1"))
                except:
                    conn.execute(text("ALTER TABLE vehicle ADD COLUMN completed_date DATETIME"))
                
                try:
                    conn.execute(text("SELECT is_active FROM vehicle LIMIT 1"))
                except:
                    conn.execute(text("ALTER TABLE vehicle ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                
                conn.commit()
                print("Schema updated successfully")
            
        except Exception as e:
            print(f"Error updating schema: {e}")
            raise

if __name__ == '__main__':
    update_schema() 