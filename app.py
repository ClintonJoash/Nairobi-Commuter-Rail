import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Function to initialize the database
def init_db():
    conn = sqlite3.connect('commuters.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commuters (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL CHECK(LENGTH(name) <= 15),
            contact_info TEXT NOT NULL UNIQUE CHECK(LENGTH(contact_info) == 10),
            CONSTRAINT contact_info_digits CHECK(contact_info GLOB '[0-9]*')
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
    
    # Insert commuter data into the database
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
    contact_info = request.form['contact_info']
    
    # Check if the commuter exists in the database
    conn = sqlite3.connect('commuters.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM commuters WHERE contact_info = ?', (contact_info,))
    commuter = cursor.fetchone()
    conn.close()
    
    if commuter:
        return redirect(url_for('booking'))
    else:
        return 'Error: Commuter not found <a href="/">Back to Home</a>'

# Route to display the booking page
@app.route('/booking')
def booking():
    return render_template('booking.html')

# Route to display the payment page
@app.route('/payment')
def payment():
    # Render the payment.html template
    return render_template('payment.html')


if __name__ == '__main__':
    app.run(debug=True)
