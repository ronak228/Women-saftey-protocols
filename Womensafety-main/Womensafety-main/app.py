from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database import init_db, get_db, close_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize Twilio client
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Initialize database
try:
    init_db()
except Exception as e:
    print(f"Warning: Database initialization failed: {str(e)}")
    print("The application will continue to run but database features may not work.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            db = get_db()
            data = request.form
            
            # Check if user already exists
            if db.users.find_one({'email': data['email']}):
                flash('Email already registered')
                return redirect(url_for('register'))
            
            # Create new user
            user = {
                'firstName': data['firstName'],
                'lastName': data['lastName'],
                'email': data['email'],
                'phone': data['phone'],
                'password': generate_password_hash(data['password']),
                'created_at': datetime.utcnow()
            }
            
            db.users.insert_one(user)
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            flash('An error occurred during registration. Please try again.')
            print(f"Registration error: {str(e)}")
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            db = get_db()
            data = request.form
            
            user = db.users.find_one({'email': data['email']})
            if user and check_password_hash(user['password'], data['password']):
                flash('Login successful!')
                return redirect(url_for('index'))
            
            flash('Invalid email or password')
            return redirect(url_for('login'))
        except Exception as e:
            flash('An error occurred during login. Please try again.')
            print(f"Login error: {str(e)}")
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/volunteer', methods=['GET', 'POST'])
def volunteer():
    if request.method == 'POST':
        try:
            db = get_db()
            data = request.form
            
            volunteer = {
                'firstName': data['firstName'],
                'lastName': data['lastName'],
                'email': data['email'],
                'phone': data['phone'],
                'experience': data['experience'],
                'availability': data['availability'],
                'created_at': datetime.utcnow()
            }
            
            db.volunteers.insert_one(volunteer)
            flash('Thank you for volunteering! We will contact you soon.')
            return redirect(url_for('index'))
        except Exception as e:
            flash('An error occurred during volunteer registration. Please try again.')
            print(f"Volunteer registration error: {str(e)}")
            return redirect(url_for('volunteer'))
    
    return render_template('volunteer.html')

@app.route('/safety-tips')
def safety_tips():
    try:
        db = get_db()
        tips = list(db.safety_tips.find({}, {'_id': 0}))
        return render_template('safety.html', tips=tips)
    except Exception as e:
        print(f"Error fetching safety tips: {str(e)}")
        return render_template('safety.html', tips=[])

@app.route('/api/safety-tips')
def get_safety_tips():
    try:
        db = get_db()
        tips = list(db.safety_tips.find({}, {'_id': 0}))
        return jsonify(tips)
    except Exception as e:
        print(f"Error fetching safety tips API: {str(e)}")
        return jsonify([])

@app.route('/api/emergency-contacts', methods=['GET', 'POST'])
def emergency_contacts():
    try:
        db = get_db()
        if request.method == 'POST':
            data = request.json
            db.emergency_contacts.insert_one(data)
            return jsonify({'message': 'Emergency contact added successfully'})
        
        contacts = list(db.emergency_contacts.find({}, {'_id': 0}))
        return jsonify(contacts)
    except Exception as e:
        print(f"Error in emergency contacts API: {str(e)}")
        return jsonify({'error': 'Failed to process request'})

# Emergency route
@app.route('/emergency')
def emergency():
    return render_template('emergency.html')

def send_emergency_sms(phone_number, message):
    try:
        if not twilio_client:
            print("Warning: Twilio is not configured. SMS will not be sent.")
            return False
            
        # Format the phone number (add '+' if not present)
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
            
        # Send SMS using Twilio
        message = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        print(f"SMS sent successfully to {phone_number}. Message SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        return False

@app.route('/trigger_sos', methods=['POST'])
def trigger_sos():
    try:
        data = request.json
        primary_contact = data.get('primary')
        secondary_contact = data.get('secondary')
        
        # Get user's location from request if available
        user_location = data.get('location', 'Location not available')
        
        # Compose emergency message
        message = f"EMERGENCY ALERT: Your contact needs immediate help! Last known location: {user_location}"
        
        # Track successful sends
        success = False
        
        # Send SMS to emergency contacts
        if primary_contact:
            if send_emergency_sms(primary_contact, message):
                success = True
                
        if secondary_contact:
            if send_emergency_sms(secondary_contact, message):
                success = True
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Emergency contacts have been notified'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send notifications. Please try again or contact emergency services directly.'
            }), 500
            
    except Exception as e:
        print(f"Error in trigger_sos: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting the Women Safety application...")
    print("Access the website at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True) 