import asyncio
import random
import aiohttp

TRAFFIC_TYPES = {
    "Instagram": {"data_rate": 10.0, "latency": 20.0},
    "WhatsApp": {"data_rate": 1.0, "latency": 50.0},
    "YouTube": {"data_rate": 50.0, "latency": 15.0},
    "Voice Call": {"data_rate": 0.5, "latency": 10.0},
    "Text Message": {"data_rate": 0.01, "latency": 100.0},
    "Voice Message": {"data_rate": 5.0, "latency": 25.0},
}

USER_DENSITIES = ["low", "medium", "high"]
TRAFFIC_LOADS = ["light", "moderate", "heavy"]

def generate_mock_data():
    traffic_type = random.choice(list(TRAFFIC_TYPES.keys()))
    characteristics = TRAFFIC_TYPES[traffic_type].copy()

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
        "user_id": random.randint(0, 19),
        "data_rate": characteristics["data_rate"],
        "latency": characteristics["latency"],
        "packet_loss": random.uniform(0.0, 5.0),
        # "user_density": user_density,
        "traffic_load": traffic_load,
        "traffic_type": traffic_type,
        "cqi": cqi
    }

async def send_packets():
    async with aiohttp.ClientSession() as session:
        while True:
            data = generate_mock_data()
            try:
                async with session.post("http://127.0.0.1:5432/process_packet/", json=data) as response:
                    if response.status == 200:
                        print(f"Sent packet data: {data}")
                    else:
                        print(f"Error sending packet data: {await response.text()}")
            except Exception as e:
                print(f"Exception occurred: {e}")
            await asyncio.sleep(1)  # Send a packet every second

if __name__ == "__main__":
    asyncio.run(send_packets())