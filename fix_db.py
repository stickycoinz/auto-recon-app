from auto_recon_app.app import app, db
from sqlalchemy import text

def fix_database():
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Create new table with correct schema
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        password_hash VARCHAR(120) NOT NULL,
                        email VARCHAR(120) UNIQUE,
                        role VARCHAR(20) DEFAULT 'ground_manager',
                        is_active BOOLEAN DEFAULT 1,
                        last_login DATETIME,
                        created_date DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Copy data from old table to new table
                try:
                    conn.execute(text("""
                        INSERT INTO user_new (id, username, password_hash)
                        SELECT id, username, password
                        FROM user
                    """))
                except Exception as e:
                    print(f"Error copying data: {e}")
                
                # Drop old table
                conn.execute(text("DROP TABLE IF EXISTS user"))
                
                # Rename new table to user
                conn.execute(text("ALTER TABLE user_new RENAME TO user"))
                
                conn.commit()
                print("Successfully recreated user table with correct schema")
        except Exception as e:
            print(f"Error fixing database: {e}")

if __name__ == '__main__':
    fix_database() 