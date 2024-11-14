from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import asyncio
import aiohttp
import random
import threading

app = Flask(__name__)
socketio = SocketIO(app, async_mode="gevent")

# Define traffic types, user densities, and traffic loads
TRAFFIC_TYPES = {
    "Instagram": {"data_rate": 10.0, "latency": 20.0},
    "WhatsApp": {"data_rate": 1.0, "latency": 50.0},
    "YouTube": {"data_rate": 50.0, "latency": 15.0},
    "Voice Call": {"data_rate": 0.5, "latency": 10.0},
    "Text Message": {"data_rate": 0.01, "latency": 100.0},
    "Voice Message": {"data_rate": 5.0, "latency": 25.0},
}

USER_DENSITIES = ["low", "medium", "high"]

# Background task control
background_task = None
task_active = False

# Adjust data characteristics based on user density
def adjust_characteristics(characteristics, user_density):
    if user_density == "medium":
        characteristics["data_rate"] *= 0.75
        characteristics["latency"] *= 1.25
    elif user_density == "high":
        characteristics["data_rate"] *= 0.5
        characteristics["latency"] *= 1.5
    return characteristics

# Generate mock packet data
def generate_mock_data(user_density, traffic_type):
    characteristics = TRAFFIC_TYPES[traffic_type].copy()
    characteristics = adjust_characteristics(characteristics, user_density)

    return {
        "user_id": random.randint(0, 19),
        "data_rate": characteristics["data_rate"],
        "latency": characteristics["latency"],
        "packet_loss": random.uniform(0.0, 5.0),
        "traffic_load": random.choice(["light", "moderate", "heavy"]),
        "traffic_type": traffic_type,
        "cqi": random.uniform(0.1, 1.0)
    }

# Background task for sending packets
async def send_packets(user_density, traffic_type):
    global task_active
    async with aiohttp.ClientSession() as session:
        while task_active:
            data = generate_mock_data(user_density, traffic_type)
            try:
                async with session.post("http://127.0.0.1:5432/process_packet/", json=data) as response:
                    if response.status == 200:
                        socketio.emit("packet_status", {"status": "sent", "data": data})
                    else:
                        socketio.emit("packet_status", {"status": "error", "data": await response.text()})
            except Exception as e:
                socketio.emit("packet_status", {"status": "exception", "data": str(e)})
            await asyncio.sleep(1)

# Routes to add and remove traffic types
@app.route("/add_traffic_type", methods=["POST"])
def add_traffic_type():
    new_type = request.json.get("type")
    data_rate = request.json.get("data_rate")
    latency = request.json.get("latency")

    if new_type and data_rate and latency:
        TRAFFIC_TYPES[new_type] = {"data_rate": data_rate, "latency": latency}
        return jsonify({"status": "added", "type": new_type, "data_rate": data_rate, "latency": latency})
    else:
        return jsonify({"error": "Invalid input"}), 400

@app.route("/remove_traffic_type", methods=["POST"])
def remove_traffic_type():
    type_to_remove = request.json.get("type")
    if type_to_remove in TRAFFIC_TYPES:
        del TRAFFIC_TYPES[type_to_remove]
        return jsonify({"status": "removed", "type": type_to_remove})
    else:
        return jsonify({"error": "Type not found"}), 404

# Start sending packets on user request
@app.route("/start", methods=["POST"])
def start_task():
    global background_task, task_active
    user_density = request.json.get("user_density")
    traffic_type = request.json.get("traffic_type")
    task_active = True

    # Run send_packets asynchronously in a new event loop
    background_task = threading.Thread(target=lambda: asyncio.run(send_packets(user_density, traffic_type)))
    background_task.start()
    return jsonify({"status": "task_started"})

# Stop sending packets on user request
@app.route("/stop", methods=["POST"])
def stop_task():
    global task_active
    task_active = False
    return jsonify({"status": "task_stopped"})

# Main route for the UI
@app.route("/")
def index():
    return render_template("index.html", traffic_types=TRAFFIC_TYPES.keys(), user_densities=USER_DENSITIES)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5006)
