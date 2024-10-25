from flask import Flask, jsonify, request, session
from datetime import datetime, timedelta
import uuid
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set a strong secret key for session management from environment variable
app.secret_key = os.getenv('SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# In-memory storage for users and sessions (this is for demo purposes, replace with actual DB in production)
users_db = {
    'testuser': {'password': os.getenv('TESTUSER_PASSWORD'), 'devices': []}  # Example user
}

# Basic status check route
@app.route('/')
def index():
    return jsonify({"message": "SignOutSync Backend Running"}), 200

# User authentication function
def authenticate(username, password):
    user = users_db.get(username)
    if user and user['password'] == password:
        return True
    return False

# User login route
@app.route('/login', methods=['POST'])
def login():
    data = request.json

    # Validate that both username, password, and device name are provided
    if 'username' not in data or 'password' not in data or 'device_name' not in data:
        return jsonify({"message": "Username, password, and device name are required!"}), 400

    username = data['username']
    password = data['password']
    device_name = data['device_name']
    device_id = str(uuid.uuid4())  # Generate a unique device identifier
    login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current time
    user_agent = request.headers.get('User-Agent')  # Get User-Agent from request headers

    # Perform authentication
    if authenticate(username, password):
        session['user'] = username
        session['device'] = device_id  # Store current device ID in the session
        session.permanent = True  # Mark the session as permanent (honors session lifetime)

        # Add the device to the user's devices list in the database
        user = users_db.get(username)
        user['devices'].append({
            'device_id': device_id,
            'device_name': device_name,
            'login_time': login_time,
            'user_agent': user_agent
        })  # Append new device to user's devices list
        return jsonify({
            "message": f"Logged in from {device_name} at {login_time}",
            "device_id": device_id,
            "user_agent": user_agent
        }), 200
    else:
        return jsonify({"message": "Invalid credentials!"}), 401

# User logout route to keep only the most recent device
@app.route('/logout', methods=['POST'])
def logout():
    if 'user' in session:
        username = session['user']
        user = users_db.get(username)

        if not user:
            return jsonify({"message": "User not found in the database!"}), 404

        # Retrieve the most recent device from the session
        most_recent_device_id = session.get('device')

        # Keep only the most recent device in the user's devices list
        user['devices'] = [device for device in user.get('devices', []) if device['device_id'] == most_recent_device_id]

        # Prepare response message
        logout_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.pop('user', None)
        session.pop('device', None)  # Clear session

        return jsonify({
            "message": f"Logged out all devices except the most recent one at {logout_time}",
            "remaining_device": user['devices']
        }), 200
    else:
        return jsonify({"message": "No active session found!"}), 401

# View active devices
@app.route('/devices', methods=['POST'])
def view_devices():
    data = request.json
    username = data.get('username')
    if not username:
        return jsonify({"message": "Username is required!"}), 400

    user = users_db.get(username)
    if user:
        return jsonify(user), 200
    return jsonify({"message": "User not found!"}), 404

if __name__ == '__main__':
    app.run(debug=True)
