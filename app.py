import sqlite3
import csv
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import requests
import base64
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = '6f64c4e71bf4f967ae9a85c281291083'

# Safaricom API credentials
CONSUMER_KEY = '5LyZXmj0n4SJADkXLtskKv4wd0BocvkuuI0aZmZGTGVVl88f'
CONSUMER_SECRET = 'QvAy9gmLz80hA65ZF1HzDstxe2LXJmBGAZoz3uOXkwiWlNVDvTHKuaEKaGROGV38'
BUSINESS_SHORT_CODE = '174379'
PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
CALLBACK_URL = 'http://127.0.0.1.com/5000'

# Path to login attempts CSV file
LOGIN_ATTEMPTS_FILE = 'login_attempts.csv'

# Ensure the login attempts CSV file exists
if not os.path.isfile(LOGIN_ATTEMPTS_FILE):
    with open(LOGIN_ATTEMPTS_FILE, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'username', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

# Initialize the database
def init_db():
    conn = sqlite3.connect('commuters.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commuters (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL CHECK(LENGTH(name) <= 15),
            contact_info TEXT NOT NULL UNIQUE CHECK(LENGTH(contact_info) = 10),
            CONSTRAINT contact_info_digits CHECK(contact_info GLOB '[0-9]*')
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            route TEXT,
            stop TEXT,
            fare REAL,
            status TEXT DEFAULT 'pending',
            payment_status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES commuters (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES commuters (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY,
            booking_id INTEGER,
            fare REAL,
            payment_method TEXT,
            payment_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            phone_number TEXT,
            payment_status TEXT DEFAULT 'pending',
            FOREIGN KEY (booking_id) REFERENCES bookings (id)
        )
    ''')
    conn.commit()
    conn.close(

# Function to get access token from Safaricom API
def get_access_token():
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    
    # Generate base64 encoded credentials
    credentials = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode('utf-8')

    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        response_data = response.json()
        return response_data['access_token']
    else:
        raise Exception(f"Failed to get access token: {response.status_code}, {response.text}")

# Function to initiate payment request to Safaricom API
def initiate_payment(token, phone_number, fare, booking_id):
    api_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode((BUSINESS_SHORT_CODE + PASSKEY + timestamp).encode()).decode('utf-8')
    
    payload = {
        'BusinessShortCode': BUSINESS_SHORT_CODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(float(fare)),
        'PartyA': phone_number,
        'PartyB': BUSINESS_SHORT_CODE,
        'PhoneNumber': phone_number,
        'CallBackURL': CALLBACK_URL,
        'AccountReference': f'NCR Booking Ticket{booking_id}',
        'TransactionDesc': 'Payment for booking'
    }

    response = requests.post(api_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to initiate payment: {response.status_code}, {response.text}")

# Log login attempt
def log_login_attempt(username, status):
    with open(LOGIN_ATTEMPTS_FILE, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'username', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({
            'timestamp': datetime.now().isoformat(),
            'username': username,
            'status': status
        })

# Initialize the database when the application starts
init_db()

# Route to display the homepage with options to log in or sign up
@app.route('/')
def index():
    return render_template('index.html')

# Route to display the registration form
@app.route('/register', methods=['GET'])
def register_form():
    return render_template('register.html')

# Route to handle the registration form submission
@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    contact_info = request.form['contact_info']
    
    conn = sqlite3.connect('commuters.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO commuters (name, contact_info) VALUES (?, ?)', (name, contact_info))
        conn.commit()
        conn.close()
        flash('Registration successful!', 'success')
        return redirect(url_for('index'))
    except sqlite3.IntegrityError:
        conn.close()
        flash('Ooops: Commuter already registered', 'error')
        return redirect(url_for('register_form'))

# Route to display the login form
@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

# Route to handle the login form submission
@app.route('/login', methods=['POST'])
def login():
    name = request.form.get('name')
    contact_info = request.form.get('contact_info')
    
    if not name or not contact_info:
        flash('Both fields are required.', 'error')
        return render_template('login.html')
    
    conn = sqlite3.connect('commuters.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM commuters WHERE name = ? AND contact_info = ?', (name, contact_info))
    commuter = cursor.fetchone()
    
    if commuter:
        session['user_id'] = commuter[0]
        log_login_attempt(name, 'successful')
        
        # Record the successful login
        cursor.execute('INSERT INTO login_attempts (user_id) VALUES (?)', (commuter[0],))
        conn.commit()
        conn.close()
        return redirect(url_for('booking'))
    else:
        log_login_attempt(name, 'unsuccessful')
        conn.close()
        flash('Invalid credentials.', 'error')
        return render_template('login.html')

# Route to display the booking page
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        route = request.form['route']
        stop = request.form['stop']
        fare = request.form['fare']
        
        if not route or not stop or not fare:
            return jsonify(success=False, error='All fields are required.')

        # Save booking info to the database
        conn = sqlite3.connect('commuters.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bookings (user_id, route, stop, fare) 
            VALUES (?, ?, ?, ?)''', 
            (session['user_id'], route, stop, fare))
        
        # Automatically generated booking_id
        booking_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"Generated Booking ID: {booking_id}")  # Debugging: Print the booking ID
        return jsonify(success=True, booking_id=booking_id)
    
    return render_template('booking.html')

# Route to display the payment page
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        fare = request.form['fare']
        booking_id = request.form['booking_id']
        
        # Validate phone number format
        if not phone_number.startswith('254') or len(phone_number) != 12 or not phone_number.isdigit():
            flash('Invalid phone number. It must be in the format 2547XXXXXXXX.', 'error')
            return render_template('payment.html', fare=fare, booking_id=booking_id)
        
        try:
            # Initiate payment
            token = get_access_token()
            response = initiate_payment(token, phone_number, fare, booking_id)

            # Determine payment status
            payment_status = 'Pending' if response.get("ResponseCode") == "0" else 'Completed'
            
            # Save payment information to the database
            conn = sqlite3.connect('commuters.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payments (booking_id, fare, payment_method, phone_number, payment_status)
                VALUES (?, ?, ?, ?, ?)
            ''', (booking_id, fare, 'mobile_money', phone_number, payment_status))
            conn.commit()
            conn.close()

            # Provide feedback and redirect to report page after confirmation
            flash('Payment initiated successfully!', 'success')
            return jsonify({'success': True, 'booking_id': booking_id})
        except requests.exceptions.HTTPError as http_err:
            flash(f'HTTP error occurred: {http_err}', 'error')
            print(f"HTTP error occurred: {http_err}")
            print(f"Response content: {http_err.response.content}")
        except requests.exceptions.RequestException as req_err:
            flash(f'Request error occurred: {req_err}', 'error')
            print(f"Request error occurred: {req_err}")
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            print(f"An error occurred: {str(e)}")
        return jsonify({'success': False})

    fare = request.args.get('fare', '')
    booking_id = request.args.get('booking_id', '')

    if not booking_id:
        flash('Booking ID is missing. Please try again.', 'error')
        return redirect(url_for('booking'))

    return render_template('payment.html', fare=fare, booking_id=booking_id)

# Route to generate the report after payment attempt
@app.route('/report/<int:booking_id>', methods=['GET'])
def report(booking_id):
    conn = sqlite3.connect('commuters.db')
    cursor = conn.cursor()
    
    # Retrieve booking and payment information
    cursor.execute('''
        SELECT c.name, p.phone_number, b.stop, p.payment_status
        FROM commuters c
        JOIN bookings b ON c.id = b.user_id
        JOIN payments p ON b.id = p.booking_id
        WHERE b.id = ?
    ''', (booking_id,))
    
    report_data = cursor.fetchone()
    conn.close()

    # Debugging: Print the fetched report data
    print("Report Data:", report_data)

    if report_data:
        return render_template('report.html', report=report_data)
    else:
        flash('No report found for this booking.', 'error')
        return redirect(url_for('index'))

# Route to display login attempts
@app.route('/login_attempts')
def login_attempts():
    attempts = []
    with open(LOGIN_ATTEMPTS_FILE, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            attempts.append(row)
    return jsonify(attempts)

# API Route to handle STK push request
@app.route('/api/payment', methods=['POST'])
def api_payment():
    data = request.json
    phone_number = data.get('phoneNumber')
    fare = data.get('fare')
    booking_id = data.get('bookingId')

    try:
        # Initiate payment using the previously defined function
        token = get_access_token()
        response = initiate_payment(token, phone_number, fare, booking_id)

        # Determine payment status
        payment_status = 'Completed' if response.get("ResponseCode") == "0" else 'Pending'
        
        # Save payment information to the database
        conn = sqlite3.connect('commuters.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payments (booking_id, fare, payment_method, phone_number, payment_status)
            VALUES (?, ?, ?, ?, ?)
        ''', (booking_id, fare, 'mobile_money', phone_number, payment_status))
        conn.commit()
        conn.close()

        # Return a success response
        return jsonify(success=True)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify(success=False), 500

if __name__ == '__main__':
    app.run(debug=True)  # Make sure to run Flask in debug mode
