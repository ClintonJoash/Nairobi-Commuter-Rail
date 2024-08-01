import sqlite3
import csv  # Import the csv module
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import base64
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = '6f64c4e71bf4f967ae9a85c281291083'

# Safaricom API credentials
CONSUMER_KEY = '5LyZXmj0n4SJADkXLtskKv4wd0BocvkuuI0aZmZGTGVVl88f'
CONSUMER_SECRET = 'QvAy9gmLz80hA65ZF1HzDstxe2LXJmBGAZoz3uOXkwiWlNVDvTHKuaEKaGROGV38'

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
    conn.commit()
    conn.close()

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
        return 'Registration successful! <a href="/">Back to Home</a>'
    except sqlite3.IntegrityError:
        conn.close()
        return 'Error: Commuter already registered <a href="/">Back to Home</a>'

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
        return render_template('login.html', error='Both fields are required.')
    
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
        return render_template('login.html', error='Invalid credentials')

# Route to display the booking page
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        route = request.form['route']
        stop = request.form['stop']
        fare = request.form['fare']
        
        if not route or not stop or not fare:
            return render_template('booking.html', error='All fields are required.')

        # Save booking info to the database
        conn = sqlite3.connect('commuters.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO bookings (user_id, route, stop, fare) VALUES (?, ?, ?, ?)', 
                       (session['user_id'], route, stop, fare))
        conn.commit()
        conn.close()
        
        return redirect(url_for('payment', fare=fare))
    
    return render_template('booking.html')

# Route to display the payment page
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        fare = request.form['fare']
        
        if not phone_number or not phone_number.isdigit() or len(phone_number) != 10 or not (phone_number.startswith('07') or phone_number.startswith('01')):
            return render_template('payment.html', error='Invalid phone number.', fare=fare)
        
        # Make payment request to Safaricom API
        try:
            token = get_access_token()
            response = initiate_payment(token, phone_number, fare)
            if response.status_code == 200:
                return render_template('payment.html', message='Payment request successful. Please check your phone.', fare=fare)
            else:
                return render_template('payment.html', error='Payment request failed.', fare=fare)
        except Exception as e:
            return render_template('payment.html', error=f'Error: {str(e)}', fare=fare)

    fare = request.args.get('fare', '')
    return render_template('payment.html', fare=fare)

# Function to get access token from Safaricom API
def get_access_token():
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()).decode('utf-8'),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = requests.get(api_url, headers=headers)
    response_data = response.json()
    return response_data['access_token']

# Function to initiate payment request to Safaricom API
def initiate_payment(token, phone_number, fare):
    api_url = ' https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl'
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    shortcode = '174379'
    lipa_na_mpesa_online_passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
    password = base64.b64encode((shortcode + lipa_na_mpesa_online_passkey + timestamp).encode()).decode('utf-8')
    
    payload = {
        'BusinessShortCode': 174379,
        'Password': 'Safaricom999!*!', # type: ignore
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': fare,
        'PartyA': 600977,
        'PartyB': 600000,
        'PhoneNumber': 254708374149,
        'CallBackURL': 'https://127.0.0.1:5000',  # Update with your callback URL
        'AccountReference': 'testapi',
        'TransactionDesc': 'Payment for test',
    }
    
    response = requests.post(api_url, json=payload, headers=headers)
    return response

@app.route('/api/payment', methods=['POST'])
def process_payment():
    data = request.json
    mobile_number = data.get('mobileNumber')
    fare = data.get('fare')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {get_access_token()}'
    }
    
    payload = {
        'ShortCode': '600977',
        'CommandID': 'CustomerBuyGoodsOnline',
        'amount': fare,
        'MSISDN': mobile_number,
        'BillRefNumber': ''
    }
    
    response = requests.post(' https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl', headers=headers, json=payload)
    
    if response.status_code == 200:
        return jsonify({'success': True, 'message': 'Payment request sent successfully.'})
    else:
        return jsonify({'success': False, 'message': 'An error occurred while making the payment.'})

# Route to display login attempts
@app.route('/login_attempts')
def login_attempts():
    attempts = []
    with open(LOGIN_ATTEMPTS_FILE, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            attempts.append(row)
    return jsonify(attempts)

if __name__ == '__main__':
    app.run(debug=True)
