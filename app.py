import base64
import requests
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = '6f64c4e71bf4f967ae9a85c281291083'

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

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET'])
def register_form():
    return render_template('register.html')

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

@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

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
        cursor.execute('INSERT INTO login_attempts (user_id) VALUES (?)', (commuter[0],))
        conn.commit()
        conn.close()
        
        return redirect(url_for('booking'))
    else:
        conn.close()
        return render_template('login.html', error='Invalid credentials')

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        route = request.form['route']
        stop = request.form['stop']
        fare = request.form['fare']
        
        if not route or not stop or not fare:
            return render_template('booking.html', error='All fields are required.')

        conn = sqlite3.connect('commuters.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO bookings (user_id, route, stop, fare) VALUES (?, ?, ?, ?)', 
                       (session['user_id'], route, stop, fare))
        conn.commit()
        conn.close()
        
        return redirect(url_for('payment', fare=fare))
    
    return render_template('booking.html')

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        
        if not phone_number or not phone_number.isdigit() or len(phone_number) != 10 or not (phone_number.startswith('07') or phone_number.startswith('01')):
            return render_template('payment.html', error='Invalid phone number.')
        
        try:
            token = get_access_token()
            response = initiate_payment(token, phone_number)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("ResponseCode") == "0":
                    return render_template('payment.html', message='Payment request successful. Please check your phone.')
                else:
                    error_message = response_data.get("ResponseDescription", "Payment request failed.")
                    return render_template('payment.html', error=error_message)
            else:
                return render_template('payment.html', error='Payment request failed.')
        except Exception as e:
            return render_template('payment.html', error=f'Error: {str(e)}')

    fare = request.args.get('fare', '')
    return render_template('payment.html', fare=fare)

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

def initiate_payment(token, phone_number):
    api_url = 'https://sandbox.safaricom.co.ke/mpesa/c2b/v1/simulate'
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "ShortCode": "600984",
        "CommandID": "CustomerBuyGoodsOnline",
        "amount": "1",
        "MSISDN": phone_number,
        "BillRefNumber": ""
    }
    
    response = requests.post(api_url, json=payload, headers=headers)
    
    # Print the response for debugging
    print(response.status_code)
    print(response.text)
    
    return response

if __name__ == '__main__':
    app.run(debug=True)
