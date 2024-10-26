import asyncio
import json
import random
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    characteristics = TRAFFIC_TYPES[traffic_type].copy()
    
    user_density = random.choice(USER_DENSITIES)
    traffic_load = random.choice(TRAFFIC_LOADS)
    cqi = random.uniform(0.1, 1.0)
    
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

@app.post("/generate-traffic")
async def generate_traffic():
    return generate_mock_data()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            command = await websocket.receive_text()
            if command == "start":
                while True:
                    data = generate_mock_data()
                    await websocket.send_json(data)
                    await asyncio.sleep(1)
                    try:
                        command = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                        if command == "stop":
                            break
                    except asyncio.TimeoutError:
                        pass
            elif command == "stop":
                await websocket.send_json({"status": "stopped"})
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)