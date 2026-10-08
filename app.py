# ============================================================
# app.py - Main Flask Backend for Healthcare Management System
# ============================================================

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'healthcare_secret_key_2024'  # Change this in production

DATABASE = 'healthcare.db'

# ─────────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────────

def get_db():
    """Connect to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows dict-like access to rows
    return conn

def init_db():
    """Create all tables and insert sample data."""
    conn = get_db()
    c = conn.cursor()

    # --- USERS TABLE ---
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,  -- admin, doctor, nurse, patient
            full_name TEXT NOT NULL,
            email TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- DOCTORS TABLE ---
    c.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            specialization TEXT,
            phone TEXT,
            available_days TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # --- PATIENTS TABLE ---
    c.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE,
            user_id INTEGER,
            date_of_birth TEXT,
            gender TEXT,
            blood_group TEXT,
            phone TEXT,
            address TEXT,
            emergency_contact TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Add patient_id column if it doesn't exist (migration for existing databases)
    try:
        c.execute("PRAGMA table_info(patients)")
        columns = [col[1] for col in c.fetchall()]
        if 'patient_id' not in columns:
            c.execute("ALTER TABLE patients ADD COLUMN patient_id TEXT UNIQUE")
            print("✓ Added patient_id column to existing patients table")
    except Exception as e:
        print(f"Note: {e}")

    # --- APPOINTMENTS TABLE ---
    c.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            appointment_date TEXT,
            appointment_time TEXT,
            reason TEXT,
            status TEXT DEFAULT 'Pending',  -- Pending, Confirmed, Completed, Cancelled
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(patient_id) REFERENCES patients(id),
            FOREIGN KEY(doctor_id) REFERENCES doctors(id)
        )
    ''')

    # --- PRESCRIPTIONS TABLE ---
    c.execute('''
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            medication TEXT,
            dosage TEXT,
            frequency TEXT,
            duration TEXT,
            notes TEXT,
            prescribed_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(patient_id) REFERENCES patients(id),
            FOREIGN KEY(doctor_id) REFERENCES doctors(id)
        )
    ''')

    # --- VITALS TABLE ---
    c.execute('''
        CREATE TABLE IF NOT EXISTS vitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            nurse_id INTEGER,
            temperature REAL,
            blood_pressure TEXT,
            pulse INTEGER,
            oxygen_level REAL,
            weight REAL,
            height REAL,
            notes TEXT,
            recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(patient_id) REFERENCES patients(id),
            FOREIGN KEY(nurse_id) REFERENCES users(id)
        )
    ''')

    conn.commit()

    # ── Insert sample data only if users table is empty ──
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        _insert_sample_data(c)
        conn.commit()

    conn.close()

def _insert_sample_data(c):
    """Insert predefined staff and patient accounts."""

    # ── ADMIN ACCOUNTS ──
    admins = [
        ('admin1', 'admin1@123', 'Ramesh Kumar', 'admin1@hospital.com'),
        ('admin2', 'admin2@123', 'Neha Sharma', 'admin2@hospital.com'),
    ]
    for username, password, full_name, email in admins:
        c.execute("INSERT INTO users (username,password,role,full_name,email) VALUES (?,?,?,?,?)",
                  (username, password, 'admin', full_name, email))

    # ── DOCTOR ACCOUNTS ──
    doctors = [
        ('doctor1', 'doc1@123', 'Dr. Arjun Sharma', 'arjun.sharma@hospital.com', 'Cardiology', '9876543210'),
        ('doctor2', 'doc2@123', 'Dr. Priya Desai', 'priya.desai@hospital.com', 'Neurology', '9876543211'),
        ('doctor3', 'doc3@123', 'Dr. Vikram Patel', 'vikram.patel@hospital.com', 'Orthopedics', '9876543212'),
        ('doctor4', 'doc4@123', 'Dr. Anjali Verma', 'anjali.verma@hospital.com', 'Pediatrics', '9876543213'),
        ('doctor5', 'doc5@123', 'Dr. Rohan Thakur', 'rohan.thakur@hospital.com', 'General Medicine', '9876543214'),
    ]
    for username, password, full_name, email, specialization, phone in doctors:
        c.execute("INSERT INTO users (username,password,role,full_name,email) VALUES (?,?,?,?,?)",
                  (username, password, 'doctor', full_name, email))
        doctor_uid = c.lastrowid
        c.execute("INSERT INTO doctors (user_id,specialization,phone,available_days) VALUES (?,?,?,?)",
                  (doctor_uid, specialization, phone, 'Mon,Tue,Wed,Thu,Fri'))

    # ── NURSE ACCOUNTS ──
    nurses = [
        ('nurse1', 'nurse1@123', 'Meera Krishnan', 'meera.k@hospital.com'),
        ('nurse2', 'nurse2@123', 'Lakshmi Iyer', 'lakshmi.i@hospital.com'),
        ('nurse3', 'nurse3@123', 'Divya Nambiar', 'divya.n@hospital.com'),
        ('nurse4', 'nurse4@123', 'Aishwarya Pillai', 'aishwarya.p@hospital.com'),
        ('nurse5', 'nurse5@123', 'Sneha Srinivasan', 'sneha.s@hospital.com'),
    ]
    for username, password, full_name, email in nurses:
        c.execute("INSERT INTO users (username,password,role,full_name,email) VALUES (?,?,?,?,?)",
                  (username, password, 'nurse', full_name, email))

    # ── PHARMACIST ACCOUNTS ──
    pharmacists = [
        ('pharma1', 'pharma1@123', 'Deepak Menon', 'deepak.m@hospital.com'),
        ('pharma2', 'pharma2@123', 'Ayesha Khan', 'ayesha.k@hospital.com'),
        ('pharma3', 'pharma3@123', 'Rajesh Kumar', 'rajesh.k@hospital.com'),
        ('pharma4', 'pharma4@123', 'Prema Sriram', 'prema.s@hospital.com'),
        ('pharma5', 'pharma5@123', 'Aman Bhat', 'aman.b@hospital.com'),
    ]
    for username, password, full_name, email in pharmacists:
        c.execute("INSERT INTO users (username,password,role,full_name,email) VALUES (?,?,?,?,?)",
                  (username, password, 'pharmacist', full_name, email))

    # ── PATIENT ACCOUNTS ──
    patients = [
        ('patient1', 'patient123', 'Arjun Kumar', 'arjun.k@email.com', '1985-06-15', 'Male', 'O+', '9001122334', '123 Marina Beach, Chennai', '9001122335'),
        ('patient2', 'patient123', 'Priya Sharma', 'priya.s@email.com', '1992-03-22', 'Female', 'A+', '9005566778', '456 Anna Salai, Chennai', '9005566779'),
        ('minionpriya26@gmail.com', 'rjsl@2628', 'Lakshmi Priya', 'priya.r@email.com', '2006-05-26', 'Female', 'O-', '9962116965', 'gandhigramam', 'Karur', '6383036505'),
    ]
    for username, password, full_name, email, dob, gender, blood_group, phone, address, emergency_contact in patients:
        c.execute("INSERT INTO users (username,password,role,full_name,email) VALUES (?,?,?,?,?)",
                  (username, password, 'patient', full_name, email))
        p_uid = c.lastrowid
        c.execute("INSERT INTO patients (user_id,date_of_birth,gender,blood_group,phone,address,emergency_contact) VALUES (?,?,?,?,?,?,?)",
                  (p_uid, dob, gender, blood_group, phone, address, emergency_contact))

    # Sample appointment, prescription, and vitals
    # Get first patient and doctor IDs
    patient_record = c.execute("SELECT id FROM patients LIMIT 1").fetchone()
    doctor_record = c.execute("SELECT id FROM doctors LIMIT 1").fetchone()
    first_nurse = c.execute("SELECT id FROM users WHERE role='nurse' LIMIT 1").fetchone()
    
    if patient_record and doctor_record and first_nurse:
        patient_id = patient_record[0]
        doctor_id = doctor_record[0]
        nurse_id = first_nurse[0]
        
        # Sample appointment
        c.execute('''INSERT INTO appointments (patient_id,doctor_id,appointment_date,appointment_time,reason,status)
                     VALUES (?,?,'2024-12-20','10:00','Routine Checkup','Confirmed')''',
                  (patient_id, doctor_id))

        # Sample prescription
        c.execute('''INSERT INTO prescriptions (patient_id,doctor_id,medication,dosage,frequency,duration,notes)
                     VALUES (?,?,'Aspirin','100mg','Once daily','30 days','Take after meals')''',
                  (patient_id, doctor_id))

        # Sample vitals
        c.execute('''INSERT INTO vitals (patient_id,nurse_id,temperature,blood_pressure,pulse,oxygen_level,weight,height,notes)
                     VALUES (?,?,98.6,'120/80',72,98.5,75.0,175.0,'Normal readings')''',
                  (patient_id, nurse_id))


# ─────────────────────────────────────────────
# DECORATORS (Access Control)
# ─────────────────────────────────────────────

def login_required(f):
    """Redirect to login if user is not logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    """Restrict a route to specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user_id']   = user['id']
            session['username']  = user['username']
            session['role']      = user['role']
            session['full_name'] = user['full_name']
            flash(f"Welcome back, {user['full_name']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm_password'].strip()

        # Validation
        if not all([full_name, username, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('register'))

        conn = get_db()
        c = conn.cursor()

        # Check if username already exists
        existing_user = c.execute(
            "SELECT id FROM users WHERE username=?", (username,)
        ).fetchone()

        if existing_user:
            flash('Username already taken. Please choose another.', 'danger')
            conn.close()
            return redirect(url_for('register'))

        try:
            # Generate unique Patient ID
            result = c.execute("SELECT COUNT(*) FROM patients").fetchone()
            patient_count = result[0] if result else 0
            generated_patient_id = f"PAT{patient_count + 1:03d}"

            # Create user account
            c.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                (username, password, 'patient', full_name)
            )
            user_id = c.lastrowid

            # Create patient record with generated ID
            # Try to insert with patient_id column
            try:
                c.execute(
                    "INSERT INTO patients (patient_id, user_id) VALUES (?, ?)",
                    (generated_patient_id, user_id)
                )
            except Exception as col_error:
                # If patient_id column doesn't exist, try without it (fallback)
                if 'patient_id' in str(col_error):
                    # Attempt to add the column and retry
                    try:
                        c.execute("ALTER TABLE patients ADD COLUMN patient_id TEXT UNIQUE")
                        c.execute(
                            "INSERT INTO patients (patient_id, user_id) VALUES (?, ?)",
                            (generated_patient_id, user_id)
                        )
                    except:
                        # Last resort: insert without patient_id
                        c.execute("INSERT INTO patients (user_id) VALUES (?)", (user_id,))
                else:
                    raise

            conn.commit()
            conn.close()

            flash(f'Account created successfully! Your Patient ID is: <strong>{generated_patient_id}</strong>. Please log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'Registration failed: {str(e)}', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')



# ─────────────────────────────────────────────
# DASHBOARD (role-based)
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    """Route to redirect to role-specific dashboard"""
    role = session.get('role')
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'doctor':
        return redirect(url_for('doctor_dashboard'))
    elif role == 'nurse':
        return redirect(url_for('nurse_dashboard'))
    elif role == 'pharmacist':
        return redirect(url_for('pharmacist_dashboard'))
    elif role == 'patient':
        return redirect(url_for('patient_dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    conn = get_db()
    stats = {
        'total_doctors':  conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
        'total_patients': conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
        'total_appts':    conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
        'pending_appts':  conn.execute("SELECT COUNT(*) FROM appointments WHERE status='Pending'").fetchone()[0],
    }
    conn.close()
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/doctor/dashboard')
@login_required
@role_required('doctor')
def doctor_dashboard():
    conn = get_db()
    doctor = conn.execute(
        "SELECT * FROM doctors WHERE user_id=?", (session['user_id'],)
    ).fetchone()
    if doctor:
        patients = conn.execute('''
            SELECT DISTINCT u.full_name, p.id, p.blood_group
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE a.doctor_id = ?
        ''', (doctor['id'],)).fetchall()
        upcoming = conn.execute('''
            SELECT a.*, u.full_name as patient_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE a.doctor_id = ? AND a.status IN ('Pending','Confirmed')
            ORDER BY a.appointment_date
            LIMIT 5
        ''', (doctor['id'],)).fetchall()
    else:
        patients, upcoming = [], []
    conn.close()
    return render_template('doctor/dashboard.html', patients=patients, upcoming=upcoming)

@app.route('/nurse/dashboard')
@login_required
@role_required('nurse')
def nurse_dashboard():
    conn = get_db()
    recent_vitals = conn.execute('''
        SELECT v.*, u.full_name as patient_name
        FROM vitals v
        JOIN patients p ON v.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        ORDER BY v.recorded_at DESC
        LIMIT 10
    ''').fetchall()
    all_patients = conn.execute(
        "SELECT p.id, u.full_name FROM patients p JOIN users u ON p.user_id=u.id"
    ).fetchall()
    conn.close()
    return render_template('nurse/dashboard.html', recent_vitals=recent_vitals, patients=all_patients)

@app.route('/patient/dashboard')
@login_required
@role_required('patient')
def patient_dashboard():
    conn = get_db()
    patient = conn.execute(
        "SELECT * FROM patients WHERE user_id=?", (session['user_id'],)
    ).fetchone()
    if patient:
        appointments = conn.execute('''
            SELECT a.*, u.full_name as doctor_name, d.specialization
            FROM appointments a
            JOIN doctors doc ON a.doctor_id = doc.id
            JOIN users u ON doc.user_id = u.id
            LEFT JOIN doctors d ON d.id = a.doctor_id
            WHERE a.patient_id = ?
            ORDER BY a.appointment_date DESC
        ''', (patient['id'],)).fetchall()
        prescriptions = conn.execute('''
            SELECT pr.*, u.full_name as doctor_name
            FROM prescriptions pr
            JOIN doctors d ON pr.doctor_id = d.id
            JOIN users u ON d.user_id = u.id
            WHERE pr.patient_id = ?
            ORDER BY pr.prescribed_date DESC
        ''', (patient['id'],)).fetchall()
    else:
        appointments, prescriptions = [], []
    conn.close()
    return render_template('patient/dashboard.html',
                           patient=patient,
                           appointments=appointments,
                           prescriptions=prescriptions)

@app.route('/pharmacist/dashboard')
@login_required
@role_required('pharmacist')
def pharmacist_dashboard():
    conn = get_db()
    recent_prescriptions = conn.execute('''  
        SELECT pr.*, u.full_name as patient_name, d.full_name as doctor_name
        FROM prescriptions pr
        JOIN patients p ON pr.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        JOIN doctors doc ON pr.doctor_id = doc.id
        JOIN users d ON doc.user_id = d.id
        ORDER BY pr.prescribed_date DESC
        LIMIT 10
    ''').fetchall()
    total_prescriptions = conn.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0]
    total_patients_with_meds = conn.execute(
        "SELECT COUNT(DISTINCT patient_id) FROM prescriptions"
    ).fetchone()[0]
    conn.close()
    return render_template('pharmacist/dashboard.html',
                           recent_prescriptions=recent_prescriptions,
                           total_prescriptions=total_prescriptions,
                           total_patients_with_meds=total_patients_with_meds)


# ─────────────────────────────────────────────
# ADMIN ROUTES
# ─────────────────────────────────────────────

@app.route('/admin/doctors')
@login_required
@role_required('admin')
def admin_doctors():
    conn = get_db()
    doctors = conn.execute('''
        SELECT u.id, u.full_name, u.email, u.username,
               d.id as doctor_id, d.specialization, d.phone, d.available_days
        FROM users u JOIN doctors d ON u.id = d.user_id
    ''').fetchall()
    conn.close()
    return render_template('admin/doctors.html', doctors=doctors)

@app.route('/admin/doctors/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_add_doctor():
    if request.method == 'POST':
        full_name      = request.form['full_name']
        username       = request.form['username']
        password       = request.form['password']
        email          = request.form['email']
        specialization = request.form['specialization']
        phone          = request.form['phone']
        available_days = ','.join(request.form.getlist('available_days'))

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username,password,role,full_name,email) VALUES (?,?,?,?,?)",
                (username, password, 'doctor', full_name, email)
            )
            uid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO doctors (user_id,specialization,phone,available_days) VALUES (?,?,?,?)",
                (uid, specialization, phone, available_days)
            )
            conn.commit()
            flash('Doctor added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
        finally:
            conn.close()
        return redirect(url_for('admin_doctors'))

    return render_template('admin/add_doctor.html')

@app.route('/admin/doctors/delete/<int:doctor_id>')
@login_required
@role_required('admin')
def admin_delete_doctor(doctor_id):
    conn = get_db()
    doc = conn.execute("SELECT user_id FROM doctors WHERE id=?", (doctor_id,)).fetchone()
    if doc:
        conn.execute("DELETE FROM doctors WHERE id=?", (doctor_id,))
        conn.execute("DELETE FROM users WHERE id=?", (doc['user_id'],))
        conn.commit()
        flash('Doctor deleted.', 'success')
    conn.close()
    return redirect(url_for('admin_doctors'))

@app.route('/admin/nurses')
@login_required
@role_required('admin')
def admin_nurses():
    conn = get_db()
    nurses = conn.execute('SELECT id, full_name, email, username FROM users WHERE role=? ORDER BY full_name',
                         ('nurse',)).fetchall()
    conn.close()
    return render_template('admin/nurses.html', nurses=nurses)

@app.route('/admin/nurses/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_add_nurse():
    if request.method == 'POST':
        full_name = request.form['full_name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form.get('phone', '')

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username,password,role,full_name,email) VALUES (?,?,?,?,?)",
                (username, password, 'nurse', full_name, email)
            )
            conn.commit()
            flash('Nurse added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
        finally:
            conn.close()
        return redirect(url_for('admin_nurses'))

    return render_template('admin/add_nurse.html')

@app.route('/admin/nurses/delete/<int:nurse_id>')
@login_required
@role_required('admin')
def admin_delete_nurse(nurse_id):
    conn = get_db()
    nurse = conn.execute("SELECT id FROM users WHERE id=? AND role=?", (nurse_id, 'nurse')).fetchone()
    if nurse:
        conn.execute("DELETE FROM users WHERE id=?", (nurse_id,))
        conn.commit()
        flash('Nurse deleted.', 'success')
    conn.close()
    return redirect(url_for('admin_nurses'))

@app.route('/admin/patients')
@login_required
@role_required('admin')
def admin_patients():
    conn = get_db()
    patients = conn.execute('''
        SELECT u.id, u.full_name, u.email, u.username,
               p.id as patient_id, p.gender, p.blood_group, p.phone, p.date_of_birth
        FROM users u JOIN patients p ON u.id = p.user_id
    ''').fetchall()
    conn.close()
    return render_template('admin/patients.html', patients=patients)

@app.route('/admin/patients/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_add_patient():
    if request.method == 'POST':
        full_name = request.form['full_name']
        username  = request.form['username']
        password  = request.form['password']
        email     = request.form['email']
        dob       = request.form['date_of_birth']
        gender    = request.form['gender']
        blood     = request.form['blood_group']
        phone     = request.form['phone']
        address   = request.form['address']
        emergency = request.form['emergency_contact']

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username,password,role,full_name,email) VALUES (?,?,?,?,?)",
                (username, password, 'patient', full_name, email)
            )
            uid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO patients (user_id,date_of_birth,gender,blood_group,phone,address,emergency_contact) VALUES (?,?,?,?,?,?,?)",
                (uid, dob, gender, blood, phone, address, emergency)
            )
            conn.commit()
            flash('Patient added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
        finally:
            conn.close()
        return redirect(url_for('admin_patients'))

    return render_template('admin/add_patient.html')

@app.route('/admin/patients/delete/<int:patient_id>')
@login_required
@role_required('admin')
def admin_delete_patient(patient_id):
    conn = get_db()
    pat = conn.execute("SELECT user_id FROM patients WHERE id=?", (patient_id,)).fetchone()
    if pat:
        conn.execute("DELETE FROM patients WHERE id=?", (patient_id,))
        conn.execute("DELETE FROM users WHERE id=?", (pat['user_id'],))
        conn.commit()
        flash('Patient deleted.', 'success')
    conn.close()
    return redirect(url_for('admin_patients'))

@app.route('/admin/appointments')
@login_required
@role_required('admin')
def admin_appointments():
    conn = get_db()
    appointments = conn.execute('''
        SELECT a.*, pu.full_name as patient_name, du.full_name as doctor_name, d.specialization
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users pu ON p.user_id = pu.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users du ON d.user_id = du.id
        ORDER BY a.appointment_date DESC
    ''').fetchall()
    conn.close()
    return render_template('admin/appointments.html', appointments=appointments)

@app.route('/admin/appointments/update/<int:appt_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_update_appointment(appt_id):
    status = request.form['status']
    conn = get_db()
    conn.execute("UPDATE appointments SET status=? WHERE id=?", (status, appt_id))
    conn.commit()
    conn.close()
    flash('Appointment status updated.', 'success')
    return redirect(url_for('admin_appointments'))


# ─────────────────────────────────────────────
# DOCTOR ROUTES
# ─────────────────────────────────────────────

@app.route('/doctor/patients')
@login_required
@role_required('doctor')
def doctor_patients():
    conn = get_db()
    doctor = conn.execute("SELECT * FROM doctors WHERE user_id=?", (session['user_id'],)).fetchone()
    patients = []
    if doctor:
        patients = conn.execute('''
            SELECT DISTINCT p.*, u.full_name, u.email
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE a.doctor_id = ?
        ''', (doctor['id'],)).fetchall()
    conn.close()
    return render_template('doctor/patients.html', patients=patients)

@app.route('/doctor/prescriptions/add', methods=['GET', 'POST'])
@login_required
@role_required('doctor')
def doctor_add_prescription():
    conn = get_db()
    doctor = conn.execute("SELECT * FROM doctors WHERE user_id=?", (session['user_id'],)).fetchone()

    if request.method == 'POST' and doctor:
        conn.execute('''
            INSERT INTO prescriptions (patient_id,doctor_id,medication,dosage,frequency,duration,notes)
            VALUES (?,?,?,?,?,?,?)
        ''', (
            request.form['patient_id'], doctor['id'],
            request.form['medication'], request.form['dosage'],
            request.form['frequency'], request.form['duration'],
            request.form['notes']
        ))
        conn.commit()
        flash('Prescription added successfully!', 'success')
        conn.close()
        return redirect(url_for('dashboard'))

    # Load patients assigned to this doctor
    patients = []
    if doctor:
        patients = conn.execute('''
            SELECT DISTINCT p.id, u.full_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE a.doctor_id = ?
        ''', (doctor['id'],)).fetchall()
    conn.close()
    return render_template('doctor/add_prescription.html', patients=patients)

@app.route('/doctor/patient/<int:patient_id>/history')
@login_required
@role_required('doctor')
def doctor_patient_history(patient_id):
    conn = get_db()
    doctor = conn.execute("SELECT * FROM doctors WHERE user_id=?", (session['user_id'],)).fetchone()
    patient = conn.execute(
        "SELECT p.*, u.full_name, u.email FROM patients p JOIN users u ON p.user_id=u.id WHERE p.id=?",
        (patient_id,)
    ).fetchone()
    prescriptions = conn.execute(
        "SELECT * FROM prescriptions WHERE patient_id=? ORDER BY prescribed_date DESC", (patient_id,)
    ).fetchall()
    vitals = conn.execute(
        "SELECT * FROM vitals WHERE patient_id=? ORDER BY recorded_at DESC", (patient_id,)
    ).fetchall()
    conn.close()
    return render_template('doctor/patient_history.html',
                           patient=patient, prescriptions=prescriptions, vitals=vitals)


# ─────────────────────────────────────────────
# NURSE ROUTES
# ─────────────────────────────────────────────

@app.route('/nurse/vitals/add', methods=['GET', 'POST'])
@login_required
@role_required('nurse')
def nurse_add_vitals():
    conn = get_db()
    if request.method == 'POST':
        conn.execute('''
            INSERT INTO vitals (patient_id,nurse_id,temperature,blood_pressure,pulse,oxygen_level,weight,height,notes)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', (
            request.form['patient_id'], session['user_id'],
            request.form['temperature'], request.form['blood_pressure'],
            request.form['pulse'], request.form['oxygen_level'],
            request.form['weight'], request.form['height'],
            request.form['notes']
        ))
        conn.commit()
        flash('Vitals recorded successfully!', 'success')
        conn.close()
        return redirect(url_for('dashboard'))

    patients = conn.execute(
        "SELECT p.id, u.full_name FROM patients p JOIN users u ON p.user_id=u.id"
    ).fetchall()
    conn.close()
    return render_template('nurse/add_vitals.html', patients=patients)

@app.route('/nurse/patient/<int:patient_id>/update', methods=['GET', 'POST'])
@login_required
@role_required('nurse')
def nurse_update_patient(patient_id):
    conn = get_db()
    patient = conn.execute(
        "SELECT p.*, u.full_name FROM patients p JOIN users u ON p.user_id=u.id WHERE p.id=?",
        (patient_id,)
    ).fetchone()

    if request.method == 'POST':
        conn.execute('''
            UPDATE patients SET phone=?, address=?, emergency_contact=? WHERE id=?
        ''', (request.form['phone'], request.form['address'],
              request.form['emergency_contact'], patient_id))
        conn.commit()
        flash('Patient details updated.', 'success')
        conn.close()
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('nurse/update_patient.html', patient=patient)


# ─────────────────────────────────────────────
# PATIENT ROUTES
# ─────────────────────────────────────────────

@app.route('/patient/appointments/book', methods=['GET', 'POST'])
@login_required
@role_required('patient')
def patient_book_appointment():
    conn = get_db()
    patient = conn.execute(
        "SELECT * FROM patients WHERE user_id=?", (session['user_id'],)
    ).fetchone()

    if request.method == 'POST' and patient:
        conn.execute('''
            INSERT INTO appointments (patient_id,doctor_id,appointment_date,appointment_time,reason,status)
            VALUES (?,?,?,?,?,'Pending')
        ''', (
            patient['id'], request.form['doctor_id'],
            request.form['appointment_date'], request.form['appointment_time'],
            request.form['reason']
        ))
        conn.commit()
        flash('Appointment booked! Awaiting confirmation.', 'success')
        conn.close()
        return redirect(url_for('dashboard'))

    doctors = conn.execute(
        "SELECT d.id, u.full_name, d.specialization, d.available_days FROM doctors d JOIN users u ON d.user_id=u.id"
    ).fetchall()
    conn.close()
    return render_template('patient/book_appointment.html', doctors=doctors)

@app.route('/patient/prescriptions')
@login_required
@role_required('patient')
def patient_prescriptions():
    conn = get_db()
    patient = conn.execute("SELECT * FROM patients WHERE user_id=?", (session['user_id'],)).fetchone()
    prescriptions = []
    if patient:
        prescriptions = conn.execute('''
            SELECT pr.*, u.full_name as doctor_name
            FROM prescriptions pr
            JOIN doctors d ON pr.doctor_id = d.id
            JOIN users u ON d.user_id = u.id
            WHERE pr.patient_id = ?
            ORDER BY pr.prescribed_date DESC
        ''', (patient['id'],)).fetchall()
    conn.close()
    return render_template('patient/prescriptions.html', prescriptions=prescriptions)


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True)