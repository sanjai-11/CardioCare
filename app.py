from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g
import sqlite3
import joblib
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key'

model = joblib.load('heart_disease_model.pkl') 

# Function to connect to SQLite database
def get_db_connection():
    conn = sqlite3.connect('database/health_records.db') 
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/search_patient')
def search_patient():
    query = request.args.get('query', '').strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()

    if session.get('user_type') == 'doctor':
        doctor_id = session['doctor_id']
        cursor.execute(
            """
            SELECT patient_id, name FROM patient
            WHERE doctor_id = ? AND LOWER(name) LIKE ?
            """, (doctor_id, f"%{query}%")
        )
    else:
        cursor.execute(
            "SELECT patient_id, name FROM patient WHERE LOWER(name) LIKE ?",
            (f"%{query}%",)
        )

    patients = cursor.fetchall()
    conn.close()

    return jsonify([dict(p) for p in patients])

@app.route('/doctor/profile')
def doctor_profile():
    if session.get('user_type') != 'doctor':
        return redirect(url_for('login'))

    doctor_id = session.get('doctor_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM doctor WHERE doctor_id = ?', (doctor_id,))
    doctor = cursor.fetchone()
    conn.close()

    return render_template('doctor_profile.html',
                           doctor_name=session['doctor_name'],
                           doctor_email=doctor['email'],
                           doctor_id=doctor_id,
                           current_page='profile',
                           user_type='doctor')

# Route for Home Page (Dashboard)
@app.route('/')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    user_type = session.get('user_type')
    doctor_name = session.get('doctor_name', 'Doctor')
    admin_name = session.get('admin_name', 'Admin')

    # Common statistics for both doctor and admin
    if user_type == 'doctor':
        doctor_id = session['doctor_id']
        # Get patient count
        cursor.execute('SELECT COUNT(*) FROM patient WHERE doctor_id = ?', (doctor_id,))
        patient_count = cursor.fetchone()[0]

        # Get heart record count
        cursor.execute('SELECT COUNT(*) FROM heart_record WHERE patient_id IN (SELECT patient_id FROM patient WHERE doctor_id = ?)', (doctor_id,))
        heart_record_count = cursor.fetchone()[0]

        # Get risk analysis count
        cursor.execute('SELECT COUNT(*) FROM risk_analysis WHERE patient_id IN (SELECT patient_id FROM patient WHERE doctor_id = ?)', (doctor_id,))
        risk_analysis_count = cursor.fetchone()[0]

        # Get gender distribution (handle both int and str)
        cursor.execute('SELECT gender, COUNT(*) as count FROM patient GROUP BY gender')
        gender_stats = cursor.fetchall()
        male_count = 0
        female_count = 0
        for stat in gender_stats:
            if str(stat['gender']) == '1':
                male_count += stat['count']
            elif str(stat['gender']) == '0':
                female_count += stat['count']

        # Get high risk patients (risk score > 0.7)
        cursor.execute('''
            SELECT COUNT(*) FROM risk_analysis 
            WHERE patient_id IN (SELECT patient_id FROM patient WHERE doctor_id = ?)
            AND risk_level > 0.7
        ''', (doctor_id,))
        high_risk_count = cursor.fetchone()[0]

        # Get blood pressure statistics
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN blood_pressure > 140 THEN 1 ELSE 0 END) as high_bp,
                SUM(CASE WHEN blood_pressure < 90 THEN 1 ELSE 0 END) as low_bp
            FROM heart_record 
            WHERE patient_id IN (SELECT patient_id FROM patient WHERE doctor_id = ?)
        ''', (doctor_id,))
        bp_stats = cursor.fetchone()
        high_bp_count = bp_stats['high_bp'] or 0
        low_bp_count = bp_stats['low_bp'] or 0

    else:
        # Admin sees all data
        cursor.execute('SELECT COUNT(*) FROM patient')
        patient_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM heart_record')
        heart_record_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM risk_analysis')
        risk_analysis_count = cursor.fetchone()[0]

        # Get gender distribution (handle both int and str)
        cursor.execute('SELECT gender, COUNT(*) as count FROM patient GROUP BY gender')
        gender_stats = cursor.fetchall()
        male_count = 0
        female_count = 0
        for stat in gender_stats:
            if str(stat['gender']) == '1':
                male_count += stat['count']
            elif str(stat['gender']) == '0':
                female_count += stat['count']

        # Get high risk patients
        cursor.execute('SELECT COUNT(*) FROM risk_analysis WHERE risk_level > 0.7')
        high_risk_count = cursor.fetchone()[0]

        # Get blood pressure statistics
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN blood_pressure > 140 THEN 1 ELSE 0 END) as high_bp,
                SUM(CASE WHEN blood_pressure < 90 THEN 1 ELSE 0 END) as low_bp
            FROM heart_record
        ''')
        bp_stats = cursor.fetchone()
        high_bp_count = bp_stats['high_bp'] or 0
        low_bp_count = bp_stats['low_bp'] or 0

    conn.close()
    return render_template('dashboard.html',
        patient_count=patient_count,
        heart_record_count=heart_record_count,
        risk_analysis_count=risk_analysis_count,
        male_count=male_count,
        female_count=female_count,
        high_risk_count=high_risk_count,
        high_bp_count=high_bp_count,
        low_bp_count=low_bp_count,
        admin_name=admin_name if user_type == 'admin' else doctor_name,
        current_page='dashboard',
        user_type=user_type)

# Route for displaying and managing 'admin' table (CRUD operations)
@app.route('/admin', methods=['GET', 'POST'])
def manage_admin():
    conn = get_db_connection()
    cursor = conn.cursor()

    # If we need to add a new admin
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        password = request.form['password']
        
        # Insert new admin record into the admin table (admin_id is automatically incremented)
        cursor.execute('INSERT INTO admin (name, email, password) VALUES (?, ?, ?)', (name, email, password))
        conn.commit()
        return redirect(url_for('manage_admin'))

    # Retrieve all admin records
    cursor.execute('SELECT * FROM admin')
    admins = cursor.fetchall()

    cursor.execute('SELECT * FROM doctor')
    doctors = cursor.fetchall()
    conn.close()

    return render_template('admin.html', admins=admins, doctors=doctors, current_page='admin', user_type=session.get('user_type'))

# Route for displaying and managing 'health_record' table
@app.route('/heart_record', methods=['GET', 'POST'])
def manage_heart_record():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        heart_rate = int(request.form['heart_rate'])
        chest_pain = int(request.form['chest_pain'])
        blood_pressure = int(request.form['blood_pressure'])
        cholesterol = int(request.form['cholesterol'])
        fbs = int(request.form['fbs'])
        ecg_results = int(request.form['ecg_results'])
        exang = int(request.form['exang'])
        oldpeak = float(request.form['oldpeak'])
        slope = int(request.form['slope'])
        thal = int(request.form['thal'])

        cursor.execute(
            'INSERT INTO heart_record (patient_id, heart_rate, chest_pain, blood_pressure, cholesterol, fbs, ecg_results, exang, oldpeak, slope, thal) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (patient_id, heart_rate, chest_pain, blood_pressure, cholesterol, fbs, ecg_results, exang, oldpeak, slope, thal)
        )

        cursor.execute("SELECT age, gender FROM patient WHERE patient_id = ? ORDER BY patient_id DESC", (patient_id,))
        patient = cursor.fetchone()
        age = patient['age']
        gender = int(patient['gender'])  # Ensure it's numeric
        ca = 0  
        # ✅ Prepare input for prediction
        input_data = np.array([[age, gender, chest_pain, blood_pressure, cholesterol,
                        fbs, ecg_results, heart_rate, exang, oldpeak, ca, slope, thal]])

        # ✅ Make prediction
        prediction = model.predict(input_data)[0]  # 0 or 1
        probability = model.predict_proba(input_data)[0][1]  # risk probability

        # ✅ Save result to risk_analysis table
        cursor.execute(
            'INSERT INTO risk_analysis (patient_id, risk_level, notes) VALUES (?, ?, ?)',
            (patient_id, probability, f'Predicted Risk: {"High" if prediction == 1 else "Low"}')
        )

        conn.commit()
        return redirect(url_for('manage_heart_record'))

    cursor.execute('SELECT * FROM heart_record ORDER BY patient_id DESC')
    records = cursor.fetchall()
    cursor.execute('SELECT * FROM patient ORDER BY patient_id DESC')
    patients = cursor.fetchall()
    conn.close()
    return render_template('heart_record.html', records=records, patients=patients, current_page='heart_record', user_type=session.get('user_type'))

# Route for displaying and managing 'patient' table
@app.route('/patient', methods=['GET', 'POST'])
def manage_patient():
    conn = get_db_connection()
    cursor = conn.cursor()

    # If we need to add a new patient
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        emergency_contact = request.form['emergency_contact']
        location = request.form['location']
        doctor_id = session.get('doctor_id')
        cursor.execute('INSERT INTO patient (name, age, gender, phone, email, emergency_contact, location, doctor_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
               (name, age, gender, phone, email, emergency_contact, location, doctor_id))
        conn.commit()
        return redirect(url_for('manage_patient'))

    if session.get('user_type') == 'doctor':
        doctor_id = session.get('doctor_id')
        cursor.execute('SELECT * FROM patient WHERE doctor_id = ? ORDER BY patient_id DESC', (doctor_id,))
    else:
        cursor.execute('SELECT * FROM patient ORDER BY patient_id DESC')
    patients = cursor.fetchall()
    conn.close()
    return render_template('patient.html', patients=patients, current_page='patient', user_type=session.get('user_type'))

# Route for editing a patient record
@app.route('/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        emergency_contact = request.form['emergency_contact']
        location = request.form['location']
        cursor.execute('UPDATE patient SET name = ?, age = ?, gender = ?, phone = ?, email = ?, emergency_contact = ?, location = ? WHERE patient_id = ?',
                       (name, age, gender, phone, email, emergency_contact, location, patient_id))
        conn.commit()
        return redirect(url_for('manage_patient'))

    cursor.execute('SELECT * FROM patient WHERE patient_id = ?', (patient_id,))
    patient = cursor.fetchone()
    conn.close()
    return render_template('edit_patient.html', patient=patient, user_type=session.get('user_type'))

# Route for deleting a patient record
@app.route('/delete_patient/<int:patient_id>', methods=['GET'])
def delete_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM patient WHERE patient_id = ?', (patient_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_patient'))


# Route for displaying and managing 'risk_analysis' table
@app.route('/risk_analysis', methods=['GET', 'POST'])
def manage_risk_analysis():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        risk_score = request.form['risk_score']
        notes = request.form['notes']
        cursor.execute('INSERT INTO risk_analysis (patient_id, risk_score, notes) VALUES (?, ?, ?)', (patient_id, risk_score, notes))
        conn.commit()
        return redirect(url_for('manage_risk_analysis'))

    cursor.execute('''
    SELECT r.analysis_id, r.patient_id, r.risk_level, r.notes, p.name AS patient_name
    FROM risk_analysis r
    JOIN patient p ON r.patient_id = p.patient_id
    ORDER BY r.analysis_id DESC
''')
    analyses = cursor.fetchall()
    cursor.execute('SELECT * FROM patient ORDER BY patient_id DESC')
    patients = cursor.fetchall()
    conn.close()
    return render_template('risk_analysis.html', analyses=analyses, patients=patients, current_page='risk_analysis', user_type=session.get('user_type'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_type' in session:
        if session['user_type'] == 'admin':
            return redirect(url_for('manage_admin'))
        elif session['user_type'] == 'doctor':
            return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()

        # Try to authenticate as admin
        cursor.execute('SELECT * FROM admin WHERE email = ? AND password = ?', (email, password))
        admin = cursor.fetchone()

        if admin:
            session['user_type'] = 'admin'
            session['admin_id'] = admin['admin_id']
            session['admin_name'] = admin['name']
            conn.close()
            return redirect(url_for('manage_admin'))

        # Try to authenticate as doctor
        cursor.execute('SELECT * FROM doctor WHERE email = ? AND password = ?', (email, password))
        doctor = cursor.fetchone()

        conn.close()
        if doctor:
            session['user_type'] = 'doctor'
            session['doctor_id'] = doctor['doctor_id']
            session['doctor_name'] = doctor['name']
            return redirect(url_for('dashboard'))

        # Invalid credentials
        flash('Invalid email or password.', 'error')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'admin_id' in session or 'doctor_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin WHERE email = ?', (email,))
        if cursor.fetchone():
            flash('Email already exists, please login!', 'error')
            conn.close()
            return redirect(url_for('signup'))
        else:
            cursor.execute('INSERT INTO admin (name, email, password) VALUES (?, ?, ?)', (name, email, password))
            conn.commit()
            conn.close()
            flash('Signed up successfully, Please login!', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'static']
    if request.endpoint not in allowed_routes and 'admin_id' not in session and 'doctor_id' not in session:
        return redirect(url_for('login'))

@app.route('/edit_risk_analysis/<int:analysis_id>', methods=['GET', 'POST'])
def edit_risk_analysis(analysis_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        risk_score = request.form['risk_score']
        notes = request.form['notes']
        cursor.execute('UPDATE risk_analysis SET patient_id = ?, risk_score = ?, notes = ? WHERE analysis_id = ?',
                       (patient_id, risk_score, notes, analysis_id))
        conn.commit()
        conn.close()
        return redirect(url_for('manage_risk_analysis'))
    cursor.execute('SELECT * FROM risk_analysis WHERE analysis_id = ?', (analysis_id,))
    analysis = cursor.fetchone()
    cursor.execute('SELECT * FROM patient')
    patients = cursor.fetchall()
    conn.close()
    # Instead of a separate edit page, render risk_analysis.html with edit mode
    return render_template('risk_analysis.html', analyses=[analysis], patients=patients, current_page='risk_analysis', edit_mode=True, edit_analysis=analysis, user_type=session.get('user_type'))

@app.route('/delete_risk_analysis/<int:analysis_id>', methods=['GET'])
def delete_risk_analysis(analysis_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM risk_analysis WHERE analysis_id = ?', (analysis_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_risk_analysis'))

@app.route('/edit_admin/<int:admin_id>', methods=['GET', 'POST'])
def edit_admin(admin_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        password = request.form['password']
        cursor.execute('UPDATE admin SET name = ?, email = ?, password = ? WHERE admin_id = ?', (name, email, password, admin_id))
        conn.commit()
        conn.close()
        return redirect(url_for('manage_admin'))
    cursor.execute('SELECT * FROM admin WHERE admin_id = ?', (admin_id,))
    admin = cursor.fetchone()
    conn.close()
    return render_template('edit_admin.html', admin=admin, current_page='admin', user_type=session.get('user_type'))

@app.route('/delete_admin/<int:admin_id>', methods=['GET'])
def delete_admin(admin_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM admin WHERE admin_id = ?', (admin_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_admin'))

@app.route('/manage_doctor', methods=['GET', 'POST'])
def manage_doctor():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        password = request.form['password']
        cursor.execute('INSERT INTO doctor (name, email, password) VALUES (?, ?, ?)', (name, email, password))
        conn.commit()
        return redirect(url_for('manage_doctor'))

    cursor.execute('SELECT * FROM doctor')
    doctors = cursor.fetchall()
    conn.close()

    return render_template('admin.html', doctors=doctors, current_page='admin', user_type=session.get('user_type'))

@app.route('/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
def edit_doctor(doctor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        password = request.form['password']
        cursor.execute('UPDATE doctor SET name = ?, email = ?, password = ? WHERE doctor_id = ?', (name, email, password, doctor_id))
        conn.commit()
        conn.close()
        return redirect(url_for('manage_doctor'))
    cursor.execute('SELECT * FROM doctor WHERE doctor_id = ?', (doctor_id,))
    doctor = cursor.fetchone()
    conn.close()
    return render_template('edit_doctor.html', doctor=doctor, current_page='admin', user_type=session.get('user_type'))

@app.route('/delete_doctor/<int:doctor_id>', methods=['GET'])
def delete_doctor(doctor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM doctor WHERE doctor_id = ?', (doctor_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_doctor'))

if __name__ == '__main__':
    app.run(debug=True)
