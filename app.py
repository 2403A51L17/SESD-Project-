# app.py
from flask import (Flask, request, redirect, url_for, session, 
                   render_template, flash, send_from_directory, get_flashed_messages)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import sqlite3
import os
from datetime import datetime

# --- App Configuration ---
app = Flask(__name__)
# IMPORTANT: Change this secret key in a real application!
app.secret_key = 'super_secret_mentorship_key_42' 
DATABASE = 'mentorship_platform.db'

# --- File Upload Configuration ---
UPLOAD_FOLDER = 'uploads' # Folder where files will be stored
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'ppt', 'pptx', 'doc', 'docx', 'mp4', 'avi', 'mov', 'mp3', 'wav', 'm4a'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# ---------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

# --- Decorator for Authentication ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You must be logged in to view this page.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Helper function ---
def allowed_file(filename):
    """Checks if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Root Route ---
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('profile'))
    return redirect(url_for('login')) # Go to login if not in session

# --- Registration ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    form_data = {}
    messages = []
    if request.method == 'POST':
        # Common fields
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        password_hash = generate_password_hash(password)
        
        conn = get_db()
        try:
            if role == 'student':
                # Student-specific fields from register.html
                student_branch = request.form.get('student_branch')
                student_year = request.form.get('student_year')
                student_semester = request.form.get('student_semester')
                
                conn.execute(
                    """INSERT INTO students (username, password_hash, email, student_branch, student_year, student_semester) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (username, password_hash, email, student_branch, student_year, student_semester)
                )
            else: # role == 'mentor'
                # Mentor-specific fields from register.html
                mentor_branch = request.form.get('mentor_branch')
                mentor_year = request.form.get('mentor_year')
                mentor_subject = request.form.get('mentor_subject')
                
                conn.execute(
                    """INSERT INTO mentors (username, password_hash, email, mentor_branch, mentor_year, mentor_subject) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (username, password_hash, email, mentor_branch, mentor_year, mentor_subject)
                )
            
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        
        except sqlite3.IntegrityError:
            flash("Registration failed: Username or Email already exists.", "danger")
            form_data = dict(request.form)  # Preserve form data on error (dict for easy Jinja access)
        except sqlite3.OperationalError as e:
            flash(f"Database error: {str(e)}", "danger")
            form_data = dict(request.form)
        finally:
            conn.close()
    
    # For GET or error render: Get any flashed messages
    messages = get_flashed_messages(with_categories=True)
    return render_template('register.html', form_data=form_data, messages=messages)

# --- Login (Email-based) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    form_data = {}
    messages = []
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        conn = get_db()
        table = 'students' if role == 'student' else 'mentors'
        user = conn.execute(f"SELECT * FROM {table} WHERE email = ?", (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = role
            return redirect(url_for('profile')) 
        else:
            flash("Login Failed. Check email, password, and role.", "danger")
            form_data = dict(request.form)
            form_data.pop('password', None)
    
    messages = get_flashed_messages(with_categories=True)
    return render_template('login.html', form_data=form_data, messages=messages)

# --- Profile Router ---
@app.route('/profile')
@login_required
def profile():
    """Redirects user to their correct profile based on role."""
    if session['role'] == 'student':
        return redirect(url_for('student_profile'))
    elif session['role'] == 'mentor':
        return redirect(url_for('mentor_profile'))
    return redirect(url_for('login')) 

# --- Student Profile (Displays Info and Files) ---
@app.route('/student/profile')
@login_required
def student_profile():
    if session.get('role') != 'student':
        flash("Access Denied", "danger")
        return redirect(url_for('profile'))
        
    conn = get_db()
    
    # 1. Get student's own data (for the dashboard)
    user_data = conn.execute("SELECT * FROM students WHERE id=?", 
                             (session['user_id'],)).fetchone()
    
    # 2. Get all uploaded files from all mentors
    files_query = """
        SELECT f.id, f.filename, f.description, f.upload_date, m.username AS mentor_name
        FROM uploaded_files f
        JOIN mentors m ON f.mentor_id = m.id
        ORDER BY f.upload_date DESC
    """
    uploaded_files = conn.execute(files_query).fetchall()
    
    conn.close()
    
    messages = get_flashed_messages(with_categories=True)
    
    return render_template('student_profile.html', user_data=user_data, uploaded_files=uploaded_files, messages=messages)

# --- Mentor Profile (Displays Info and Upload Form) ---
@app.route('/mentor/profile')
@login_required
def mentor_profile():
    if session.get('role') != 'mentor':
        flash("Access Denied", "danger")
        return redirect(url_for('profile'))
        
    conn = get_db()
    user_data = conn.execute("SELECT * FROM mentors WHERE id=?", 
                             (session['user_id'],)).fetchone()
    conn.close()
    
    messages = get_flashed_messages(with_categories=True)

    return render_template('mentor_profile.html', user_data=user_data, messages=messages)

# --- Handle File Uploads ---
@app.route('/upload_material', methods=['POST'])
@login_required
def upload_material():
    if session.get('role') != 'mentor':
        flash("Only mentors can upload files.", "danger")
        return redirect(url_for('profile'))

    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('mentor_profile'))

    file = request.files['file']
    description = request.form.get('file_description', 'No description')

    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('mentor_profile'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if os.path.exists(save_path):
             flash('A file with this name already exists. Please rename your file and try again.', 'warning')
             return redirect(url_for('mentor_profile'))

        file.save(save_path)
        
        # --- Save file info to database ---
        conn = get_db()
        try:
            conn.execute(
                """INSERT INTO uploaded_files (mentor_id, filename, description, upload_date)
                   VALUES (?, ?, ?, ?)""",
                (session['user_id'], filename, description, datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
            flash('File uploaded successfully!', 'success')
        except Exception as e:
            flash(f'An error occurred while saving to database: {e}', 'danger')
        finally:
            conn.close()
            
    else:
        flash('File type not allowed. Please check the allowed extensions.', 'danger')

    return redirect(url_for('mentor_profile')) # Go back to mentor profile

# --- Handle File Downloads ---
@app.route('/download/<filename>')
@login_required
def download_file(filename):
    """Serves a file for download."""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        flash("File not found.", "danger")
        if session.get('role') == 'student':
            return redirect(url_for('student_profile'))
        else:
            return redirect(url_for('mentor_profile'))

# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)