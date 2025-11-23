# db_setup.py
import sqlite3

def create_db_and_tables():
    """Connects to/creates the DB and all necessary tables."""
    
    # Connect to SQLite database (creates the file if it doesn't exist)
    conn = sqlite3.connect('mentorship_platform.db')
    cursor = conn.cursor()

    # 1. Students Table
    # Includes fields from the registration form
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        student_branch TEXT,
        student_year TEXT,
        student_semester TEXT,
        
        -- These fields were in the original student_profile.html, 
        -- but were removed. You can add them back if needed.
        course TEXT,
        interests TEXT,
        goals TEXT
    );
    """)

    # 2. Mentors Table
    # Includes fields from the registration form
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mentors (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        mentor_branch TEXT,
        mentor_year TEXT,  -- Added for teaching year
        mentor_subject TEXT,  -- Added for assigned subject
        
        -- These fields were in the original mentor_profile.html,
        -- but were removed. You can add them back if needed.
        expertise TEXT,
        availability TEXT
    );
    """)

    # 3. Uploaded Files Table
    # This table stores a record of each uploaded file
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS uploaded_files (
        id INTEGER PRIMARY KEY,
        mentor_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        description TEXT,
        upload_date TEXT NOT NULL,
        FOREIGN KEY (mentor_id) REFERENCES mentors (id)
    );
    """)

    conn.commit()
    conn.close()
    print("Database 'mentorship_platform.db' and tables created/updated successfully.")

if __name__ == '__main__':
    create_db_and_tables()