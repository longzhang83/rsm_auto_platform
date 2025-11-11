"""
Migration script to add code_type column to verification_codes table
"""
import sqlite3
import os

# Database path
db_path = "rsm_auto_platform.db"

def migrate():
    """Add code_type column to verification_codes table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(verification_codes)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'code_type' not in columns:
            print("Adding code_type column to verification_codes table...")
            # Add the column with default value
            cursor.execute("""
                ALTER TABLE verification_codes
                ADD COLUMN code_type VARCHAR(20) DEFAULT 'register' NOT NULL
            """)
            conn.commit()
            print("Successfully added code_type column")
        else:
            print("code_type column already exists")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    if os.path.exists(db_path):
        migrate()
    else:
        print(f"Database file {db_path} not found")
