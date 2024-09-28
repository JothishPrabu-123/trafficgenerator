import asyncio
import websockets
import json
import random
import time

# Define traffic types and their characteristics
TRAFFIC_TYPES = {
    "Instagram": {"data_rate": 10.0, "latency": 20.0, "priority": "medium", "service_type": "NRT"},
    "WhatsApp": {"data_rate": 1.0, "latency": 50.0, "priority": "low", "service_type": "NRT"},
    "YouTube": {"data_rate": 50.0, "latency": 15.0, "priority": "high", "service_type": "RT"},
    "Voice Call": {"data_rate": 0.5, "latency": 10.0, "priority": "high", "service_type": "RT"},
    "Text Message": {"data_rate": 0.01, "latency": 100.0, "priority": "low", "service_type": "NRT"},
    "Voice Message": {"data_rate": 5.0, "latency": 25.0, "priority": "medium", "service_type": "NRT"},
}

USER_DENSITIES = ["low", "medium", "high"]
TRAFFIC_LOADS = ["light", "moderate", "heavy"]

def generate_mock_data():
    traffic_type = random.choice(list(TRAFFIC_TYPES.keys()))
    characteristics = TRAFFIC_TYPES[traffic_type]
    
    user_density = random.choice(USER_DENSITIES)
    traffic_load = random.choice(TRAFFIC_LOADS)
    cqi = random.uniform(0.1, 1.0)  # CQI value between 0.1 and 1.0
    
    # Adjust characteristics based on user density and traffic load
    if user_density == "medium":
        characteristics["data_rate"] *= 0.75
        characteristics["latency"] *= 1.25
    elif user_density == "high":
        characteristics["data_rate"] *= 0.5
        characteristics["latency"] *= 1.5
    
    return {
        "timestamp": time.time(),
        "user_id": random.randint(1, 20),
        "traffic_type": traffic_type,
        "data_rate": characteristics["data_rate"],
        "latency": characteristics["latency"],
        "priority": characteristics["priority"],
        "service_type": characteristics["service_type"],
        "packet_loss": random.uniform(0.0, 5.0),
        "user_density": user_density,
        "traffic_load": traffic_load,
        "cqi": cqi
    }

async def send_data(websocket, path):
    while True:
        data = generate_mock_data()
        try:
            await websocket.send(json.dumps(data))
            print(f"Sent data: {data}")
            await asyncio.sleep(1)  # Sending data every second
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection closed: {e}")
            break
        except Exception as e:
            print(f"Error sending data: {e}")

start_server = websockets.serve(send_data, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
