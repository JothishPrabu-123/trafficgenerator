import asyncio
import websockets
import json
from rl_scheduler import RLScheduler  # Import your RLScheduler class

async def receive_data_with_rl_scheduler():
    rl_scheduler = RLScheduler(num_users=20)  # Example with 20 users
    uri = "ws://localhost:6789"
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            # Use the RL scheduler to process the incoming data
            action = rl_scheduler.add_to_queue(data)

            # Periodically compute and print statistics
            if rl_scheduler.count % 10 == 0:  # Every 10 messages
                stats = rl_scheduler.compute_statistics()
                print("\nRunning RL-based Scheduler...\n")
                print(f"Service Name: {data['traffic_type']}")
                print(f"Service Type: {data['service_type']}")
                print(f"Throughput: {stats['throughput']:.2f} Mbps")
                print(f"Average Latency: {stats['average_latency']:.2f} ms")
                print(f"Average Packet Loss: {stats['average_packet_loss']:.2f} %\n")
                
                for density, traffic in rl_scheduler.user_density_data.items():
                    if traffic:
                        avg_throughput = sum(d['data_rate'] for d in traffic) / len(traffic)
                        avg_latency = sum(d['latency'] for d in traffic) / len(traffic)
                        avg_packet_loss = sum(d['packet_loss'] for d in traffic) / len(traffic)
                        print(f"User Density: {density}")
                        print(f"Throughput: {avg_throughput:.2f} Mbps")
                        print(f"Average Latency: {avg_latency:.2f} ms")
                        print(f"Average Packet Loss: {avg_packet_loss:.2f} %\n")

                for load, traffic in rl_scheduler.traffic_load_data.items():
                    if traffic:
                        avg_throughput = sum(d['data_rate'] for d in traffic) / len(traffic)
                        avg_latency = sum(d['latency'] for d in traffic) / len(traffic)
                        avg_packet_loss = sum(d['packet_loss'] for d in traffic) / len(traffic)
                        print(f"Traffic Load: {load}")
                        print(f"Throughput: {avg_throughput:.2f} Mbps")
                        print(f"Average Latency: {avg_latency:.2f} ms")
                        print(f"Average Packet Loss: {avg_packet_loss:.2f} %\n")

                print(f"Fairness Index: {stats['fairness_index']:.2f}\n")

# Start receiving data with the RL scheduler
asyncio.get_event_loop().run_until_complete(receive_data_with_rl_scheduler())
