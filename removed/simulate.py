from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import os
import random
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access
socketio = SocketIO(app, cors_allowed_origins="*")

# Default traffic types
DEFAULT_TRAFFIC_TYPES = {
    "Instagram": {"data_rate": 10.0, "latency": 20.0, "priority": "medium", "service_type": "NRT"},
    "WhatsApp": {"data_rate": 1.0, "latency": 50.0, "priority": "low", "service_type": "NRT"},
    "YouTube": {"data_rate": 50.0, "latency": 15.0, "priority": "high", "service_type": "RT"},
    "Voice Call": {"data_rate": 0.5, "latency": 10.0, "priority": "high", "service_type": "RT"},
    "Text Message": {"data_rate": 0.01, "latency": 100.0, "priority": "low", "service_type": "NRT"},
    "Voice Message": {"data_rate": 5.0, "latency": 25.0, "priority": "medium", "service_type": "NRT"},
    "Video Call": {"data_rate": 25.0, "latency": 30.0, "priority": "high", "service_type": "RT"},
    "Gaming": {"data_rate": 40.0, "latency": 10.0, "priority": "high", "service_type": "RT"},
    "Email": {"data_rate": 0.1, "latency": 70.0, "priority": "low", "service_type": "NRT"},
    "Browsing": {"data_rate": 2.0, "latency": 40.0, "priority": "medium", "service_type": "NRT"}
}

# Load or initialize configuration
CONFIG_FILE = 'traffic_config.json'
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
else:
    config = {"traffic_types": {}, "num_users": 0}

streaming = False  # Flag to manage streaming state

# Route to get current configuration and default traffic types
@app.route('/config', methods=['GET'])
def get_config():
    return jsonify({"config": config, "default_traffic_types": DEFAULT_TRAFFIC_TYPES})

# Route to add a traffic type from default list
@app.route('/add_traffic_type', methods=['POST'])
def add_traffic_type():
    data = request.json
    name = data.get('name')
    if name in DEFAULT_TRAFFIC_TYPES:
        config["traffic_types"][name] = DEFAULT_TRAFFIC_TYPES[name]
        return jsonify({"message": f"Traffic type '{name}' added successfully", "config": config})
    return jsonify({"error": f"Traffic type '{name}' is not in the default list"}), 404

# Route to remove a traffic type
@app.route('/remove_traffic_type', methods=['POST'])
def remove_traffic_type():
    name = request.json.get('name')
    if name in config["traffic_types"]:
        del config["traffic_types"][name]
        return jsonify({"message": f"Traffic type '{name}' removed successfully", "config": config})
    else:
        return jsonify({"error": f"Traffic type '{name}' not found in configuration"}), 404

# Route to set the number of users
@app.route('/set_user_count', methods=['POST'])
def set_user_count():
    num_users = request.json.get('num_users')
    config["num_users"] = num_users
    return jsonify({"message": "User count updated successfully", "config": config})

# Route to save the current configuration and start streaming
@app.route('/save_config', methods=['POST'])
def save_config():
    global streaming
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
    streaming = True  # Start streaming on save
    return jsonify({"message": "Configuration saved successfully"})

# Stream traffic data based on saved configuration
@socketio.on('start_stream')
def start_stream():
    global streaming
    while streaming:
        for traffic_type, details in config["traffic_types"].items():
            data = {
                "traffic_type": traffic_type,
                "data_rate": details["data_rate"],
                "latency": details["latency"],
                "priority": details["priority"],
                "service_type": details["service_type"],
                "user_id": random.randint(1, config["num_users"]),
                "packet_loss": round(random.uniform(0, 5), 2),
                "timestamp": time.time()
            }
            emit('traffic_data', data)
            time.sleep(1)  # Send data every second

# Stop streaming when disconnected
@socketio.on('disconnect')
def stop_stream():
    global streaming
    streaming = False

# Run the app
if __name__ == '__main__':
    socketio.run(app, debug=True,port=5532)