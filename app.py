import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, send_file
import requests
import base64
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secure secret key for session management

# Function to initialize the database
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
        
        # Record the successful login
        cursor.execute('INSERT INTO login_attempts (user_id) VALUES (?)', (commuter[0],))
        conn.commit()
        conn.close()
        
        return redirect(url_for('booking'))
    else:
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
        
        if not phone_number or not phone_number.isdigit() or len(phone_number) != 10 or not (phone_number.startswith('07') or phone_number.startswith('01')):
            return render_template('payment.html', error='Invalid phone number.')
        
        # Make payment request to Safaricom API
        try:
            token = get_access_token()
            response = initiate_payment(token, phone_number)
            if response.status_code == 200:
                return render_template('payment.html', message='Payment request successful. Please check your phone.')
            else:
                return render_template('payment.html', error='Payment request failed.')
        except Exception as e:
            return render_template('payment.html', error=f'Error: {str(e)}')

    fare = request.args.get('fare', '')
    return render_template('payment.html', fare=fare)

# Function to get access token from Safaricom API
def get_access_token():
    consumer_key = '5LyZXmj0n4SJADkXLtskKv4wd0BocvkuuI0aZmZGTGVVl88f'
    consumer_secret = 'QvAy9gmLz80hA65ZF1HzDstxe2LXJmBGAZoz3uOXkwiWlNVDvTHKuaEKaGROGV38'
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode('utf-8'),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = requests.get(api_url, headers=headers)
    response_data = response.json()
    return response_data['access_token']

# Function to initiate payment request to Safaricom API
def initiate_payment(token, phone_number):
    api_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'BusinessShortCode': '174379',
        'Password': 'your_password',  # This is a placeholder. Replace with actual password.
        'Timestamp': datetime.now().strftime('%Y%m%d%H%M%S'),
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': '1',  # Replace with the actual amount
        'PartyA': phone_number,
        'PartyB': '174379',
        'PhoneNumber': phone_number,
        'CallBackURL': 'https://example.com/callback',
        'AccountReference': 'Test123',
        'TransactionDesc': 'Payment for test'
    }
    
    response = requests.post(api_url, json=payload, headers=headers)
    return response

# Route to generate and download the report
@app.route('/generate_report')
def generate_report():
    conn = sqlite3.connect('commuters.db')
    cursor = conn.cursor()
    cursor.execute('SELECT c.name, c.contact_info, l.login_time FROM login_attempts l JOIN commuters c ON l.user_id = c.id')
    login_attempts = cursor.fetchall()
    conn.close()

    # Generate CSV file
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Contact Info', 'Login Time'])
    writer.writerows(login_attempts)
    output.seek(0)
    
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', attachment_filename='login_attempts_report.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
