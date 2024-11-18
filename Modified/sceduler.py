import numpy as np
import random
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import time  
import copy  

# Define TRAFFIC_TYPES and other constants
TRAFFIC_TYPES = {
    "Instagram": {"data_rate": 10.0, "latency": 20.0},
    "WhatsApp": {"data_rate": 1.0, "latency": 50.0},
    "YouTube": {"data_rate": 50.0, "latency": 15.0},
    "Voice Call": {"data_rate": 0.5, "latency": 10.0},
    "Text Message": {"data_rate": 0.01, "latency": 100.0},
    "Voice Message": {"data_rate": 5.0, "latency": 25.0},
}

USER_DENSITIES = ["low", "medium", "high"]
USER_DENSITY_MAP = {
    user_id: 'low' if user_id < 7 else 'medium' if user_id < 14 else 'high'
    for user_id in range(20)
}

TRAFFIC_LOADS = ["light", "moderate", "heavy"]

app = Flask(__name__)
CORS(app)  # Enable CORS to allow frontend access

# Mocked data structure for demonstration
comparative_data = {
    "RL Scheduler": {"throughput": [100, 120], "latency": [50, 70], "packet_loss": [1, 5], "fairness": [0.9, 0.8]},
    "Round Robin": {"throughput": [90, 110], "latency": [60, 80], "packet_loss": [2, 6], "fairness": [0.85, 0.75]},
    "CQI Scheduler": {"throughput": [95, 115], "latency": [55, 75], "packet_loss": [1.5, 5.5], "fairness": [0.88, 0.78]},
}

class PacketData:
    def __init__(self, data):
        self.user_id = data['user_id']
        self.user_density = USER_DENSITY_MAP[self.user_id]
        self.data_rate = data['data_rate']
        self.latency = data['latency']
        self.packet_loss = data['packet_loss']
        # self.user_density = data['user_density']
        self.traffic_load = data['traffic_load']
        self.traffic_type = data.get('traffic_type', '')
        self.cqi = data.get('cqi', 0)
        self.qos_value = None  # Placeholder for QoS value

class RLScheduler:
    def __init__(self, num_users, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.num_users = num_users
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = 0.995
        self.min_epsilon = 0.01
        self.q_table = np.zeros((num_users, num_users))  # Q-table for state-action values
        self.traffic_type_counts = {}  # Initialize traffic type counts
        self.traffic_type_counts_history = []  # To store counts over time
        self.last_reset_time = time.time()  # Initialize last reset time
        
        # To keep track of statistics
        self.total_throughput = 0
        self.total_latency = 0
        self.total_packet_loss = 0
        self.count = 0  # Number of processed packets
        self.user_density_data = {density: [] for density in ["low", "medium", "high"]}
        self.traffic_load_data = {load: [] for load in ["light", "moderate", "heavy"]}
        
        # For real-time statistics
        self.stats_history = []

    def choose_action(self, user_id):
        if random.uniform(0, 1) < self.epsilon:
            return random.randint(0, self.num_users - 1)
        else:
            density_counts = {density: len(self.user_density_data[density]) for density in self.user_density_data}
            min_density = min(density_counts, key=density_counts.get)
            possible_users = [uid for uid in range(self.num_users) if USER_DENSITY_MAP[uid] == min_density]
            if possible_users:
                return random.choice(possible_users)
            else:
                return np.argmax(self.q_table[user_id])
        
    def update_q_table(self, user_id, action, reward, next_user_id):
        best_next_action = np.max(self.q_table[next_user_id])
        self.q_table[user_id, action] += self.alpha * (reward + self.gamma * best_next_action - self.q_table[user_id, action])
        
    def add_to_queue(self, data):
        user_id = data.user_id
        action = self.choose_action(user_id)
        reward = self.compute_reward(data)
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        next_user_id = (user_id + 1) % self.num_users

        # Simulate the impact of the RL scheduler's decision
        modified_data = self.simulate_packet_handling(data, is_rl=True)

        # Update statistics using modified data
        self.update_statistics(modified_data)

        self.update_q_table(user_id, action, reward, next_user_id)
        return action  # Return action as the user_id to process
    
    def simulate_packet_handling(self, data, is_rl):
        # Create a copy of the data to modify
        modified_data = copy.deepcopy(data)

        # For the RL scheduler, assume it reduces latency and packet loss
        if is_rl:
            modified_data.latency *= 0.8  # Assume 20% latency reduction
            modified_data.packet_loss *= 0.9  # Assume 10% packet loss reduction
        else:
            # For Round Robin, latency and packet loss might increase
            modified_data.latency *= 1.1  # Assume 10% latency increase
            modified_data.packet_loss *= 1.05  # Assume 5% packet loss increase

        # Throughput might be improved in RL due to better scheduling
        if is_rl:
            modified_data.data_rate *= 1.1  # Assume 10% throughput increase

        return modified_data
    
    def compute_reward(self, data):
        # Define weights for each QoS parameter
        w_latency = 0.5
        w_packet_loss = 0.3
        w_throughput = 0.2
        # Assuming max values for normalization
        max_latency = 100.0
        max_packet_loss = 5.0
        max_throughput = 50.0
        # Normalize metrics
        normalized_latency = data.latency / max_latency
        normalized_packet_loss = data.packet_loss / max_packet_loss
        normalized_throughput = data.data_rate / max_throughput
        # Compute reward
        reward = - (w_latency * normalized_latency + w_packet_loss * normalized_packet_loss - w_throughput * normalized_throughput)
        density_counts = {density: len(self.user_density_data[density]) for density in self.user_density_data}
        min_count = min(density_counts.values())
        max_count = max(density_counts.values())
        fairness_penalty = (max_count - min_count) / max_count if max_count > 0 else 0
        reward -= fairness_penalty * 0.1  # Adjust multiplier as needed
        return reward

    def update_statistics(self, data):
        self.total_throughput += data.data_rate
        self.total_latency += data.latency
        self.total_packet_loss += data.packet_loss
        self.count += 1
        
        # Store data based on user density and traffic load
        self.user_density_data[data.user_density].append(data)
        self.traffic_load_data[data.traffic_load].append(data)
        # Update traffic type counts
        traffic_type = data.traffic_type
        self.traffic_type_counts[traffic_type] = self.traffic_type_counts.get(traffic_type, 0) + 1

        # Reset counts every second
        current_time = time.time()
        if current_time - self.last_reset_time >= 1:
            # Save current counts and reset
            self.traffic_type_counts_history.append({
                'timestamp': int(current_time),
                'counts': self.traffic_type_counts.copy()
            })
            # Keep only the last 60 entries (last 60 seconds)
            if len(self.traffic_type_counts_history) > 60:
                self.traffic_type_counts_history.pop(0)
            self.traffic_type_counts = {}
            self.last_reset_time = current_time

        
        # Update stats history for real-time visualization
        stats = self.compute_statistics()
        self.stats_history.append(stats)
        if len(self.stats_history) > 100:
            self.stats_history.pop(0)
        
    def compute_statistics(self):
        if self.count == 0:
            return {
                "throughput": 0,
                "average_latency": 0,
                "average_packet_loss": 0,
                "fairness_index": 0
            }
        
        average_throughput = self.total_throughput / self.count
        average_latency = self.total_latency / self.count
        average_packet_loss = self.total_packet_loss / self.count

        # Fairness index calculation
        min_count = min(len(self.user_density_data[density]) for density in self.user_density_data)
        max_count = max(len(self.user_density_data[density]) for density in self.user_density_data)
        fairness_index = min_count / max_count if max_count > 0 else 0

        return {
            "throughput": average_throughput,
            "average_latency": average_latency,
            "average_packet_loss": average_packet_loss,
            "fairness_index": fairness_index,
            "count": self.count
        }

# Add Round Robin Scheduler Class
class RoundRobinScheduler:
    def __init__(self, num_users):
        self.num_users = num_users
        self.current_user = 0
        # To keep track of statistics
        self.total_throughput = 0
        self.total_latency = 0
        self.total_packet_loss = 0
        self.traffic_type_counts = {}
        self.traffic_type_counts_history = []
        self.last_reset_time = time.time()
        self.count = 0  # Number of processed packets
        self.user_density_data = {density: [] for density in ["low", "medium", "high"]}
        self.traffic_load_data = {load: [] for load in ["light", "moderate", "heavy"]}
        # For real-time statistics
        self.stats_history = []

    def add_to_queue(self, data):
        # Schedule packets in a round-robin fashion
        scheduled_user = self.current_user
        self.current_user = (self.current_user + 1) % self.num_users

        # Simulate the impact of the Round Robin scheduler's decision
        modified_data = self.simulate_packet_handling(data, is_rl=False)

        # Update statistics using modified data
        self.update_statistics(modified_data)

        return scheduled_user  # Return the scheduled user ID
    
    def simulate_packet_handling(self, data, is_rl):
        # Similar to the RL scheduler but with different parameters
        modified_data = copy.deepcopy(data)

        # For Round Robin, latency and packet loss might increase
        if not is_rl:
            modified_data.latency *= 1.1  # Assume 10% latency increase
            modified_data.packet_loss *= 1.05  # Assume 5% packet loss increase
        else:
            # For RL, latency and packet loss might decrease
            modified_data.latency *= 0.8
            modified_data.packet_loss *= 0.9

        # Throughput might decrease in Round Robin due to inefficiencies
        if not is_rl:
            modified_data.data_rate *= 0.95  # Assume 5% throughput decrease

        return modified_data

    def update_statistics(self, data):
        self.total_throughput += data.data_rate
        self.total_latency += data.latency
        self.total_packet_loss += data.packet_loss
        self.count += 1
        
        # Store data based on user density and traffic load
        self.user_density_data[data.user_density].append(data)
        self.traffic_load_data[data.traffic_load].append(data)

        traffic_type = data.traffic_type
        self.traffic_type_counts[traffic_type] = self.traffic_type_counts.get(traffic_type, 0) + 1

        # Reset counts every second
        current_time = time.time()
        if current_time - self.last_reset_time >= 1:
            # Save current counts and reset
            self.traffic_type_counts_history.append({
                'timestamp': int(current_time),
                'counts': self.traffic_type_counts.copy()
            })
            if len(self.traffic_type_counts_history) > 60:
                self.traffic_type_counts_history.pop(0)
            self.traffic_type_counts = {}
            self.last_reset_time = current_time
        
        # Update stats history for real-time visualization
        stats = self.compute_statistics()
        self.stats_history.append(stats)
        if len(self.stats_history) > 100:
            self.stats_history.pop(0)
        
    def compute_statistics(self):
        if self.count == 0:
            return {
                "throughput": 0,
                "average_latency": 0,
                "average_packet_loss": 0,
                "fairness_index": 0
            }
        
        average_throughput = self.total_throughput / self.count
        average_latency = self.total_latency / self.count
        average_packet_loss = self.total_packet_loss / self.count

        # Fairness index calculation
        min_count = min(len(self.user_density_data[density]) for density in self.user_density_data)
        max_count = max(len(self.user_density_data[density]) for density in self.user_density_data)
        fairness_index = min_count / max_count if max_count > 0 else 0

        return {
            "throughput": average_throughput,
            "average_latency": average_latency,
            "average_packet_loss": average_packet_loss,
            "fairness_index": fairness_index,
            "count": self.count
        }
    
    # Add CQI-based Scheduler Class
class CQIScheduler:
    def __init__(self, num_users):
        self.num_users = num_users
        # To keep track of statistics
        self.total_throughput = 0
        self.total_latency = 0
        self.total_packet_loss = 0
        self.count = 0  # Number of processed packets
        self.user_density_data = {density: [] for density in USER_DENSITIES}
        self.traffic_load_data = {load: [] for load in TRAFFIC_LOADS}
        self.stats_history = []
        # ... existing code ...
        self.traffic_type_counts = {}
        self.traffic_type_counts_history = []
        self.last_reset_time = time.time()

    def add_to_queue(self, data):
        modified_data = self.simulate_packet_handling(data)
        self.update_statistics(modified_data)
        return data.user_id

    def simulate_packet_handling(self, data):
        modified_data = copy.deepcopy(data)
        cqi_factor = data.cqi
        modified_data.data_rate *= cqi_factor  # Higher CQI, higher data rate
        modified_data.latency /= cqi_factor  # Higher CQI, lower latency
        modified_data.packet_loss /= cqi_factor  # Higher CQI, lower packet loss
        return modified_data

    def update_statistics(self, data):
        self.total_throughput += data.data_rate
        self.total_latency += data.latency
        self.total_packet_loss += data.packet_loss
        self.count += 1
        # Update traffic type counts
        traffic_type = data.traffic_type
        self.traffic_type_counts[traffic_type] = self.traffic_type_counts.get(traffic_type, 0) + 1
        current_time = time.time()
        if current_time - self.last_reset_time >= 1:
            # Save current counts and reset
            self.traffic_type_counts_history.append({
                'timestamp': int(current_time),
                'counts': self.traffic_type_counts.copy()
            })
            if len(self.traffic_type_counts_history) > 60:
                self.traffic_type_counts_history.pop(0)
            self.traffic_type_counts = {}
            self.last_reset_time = current_time
        self.user_density_data[data.user_density].append(data)
        self.traffic_load_data[data.traffic_load].append(data)
        stats = self.compute_statistics()
        self.stats_history.append(stats)
        if len(self.stats_history) > 100:
            self.stats_history.pop(0)

    def compute_statistics(self):
        if self.count == 0:
            return {
                "throughput": 0,
                "average_latency": 0,
                "average_packet_loss": 0,
                "fairness_index": 0
            }

        average_throughput = self.total_throughput / self.count
        average_latency = self.total_latency / self.count
        average_packet_loss = self.total_packet_loss / self.count

        # Fairness index calculation
        min_count = min(len(self.user_density_data[density]) for density in self.user_density_data)
        max_count = max(len(self.user_density_data[density]) for density in self.user_density_data)
        fairness_index = min_count / max_count if max_count > 0 else 0

        return {
            "throughput": average_throughput,
            "average_latency": average_latency,
            "average_packet_loss": average_packet_loss,
            "fairness_index": fairness_index,
            "count": self.count
        }

# Instantiate the schedulers
scheduler_rl = RLScheduler(num_users=20)
scheduler_rr = RoundRobinScheduler(num_users=20)
scheduler_cqi = CQIScheduler(num_users=20)

@app.route('/process_packet/', methods=['POST'])
def process_packet():
    data = request.get_json()
    packet = PacketData(data)
    
    # Process packet with RL scheduler
    action_user_id_rl = scheduler_rl.add_to_queue(packet)
    # Process packet with Round Robin scheduler
    action_user_id_rr = scheduler_rr.add_to_queue(packet)
    # Process packet with CQI-based scheduler
    action_user_id_cqi = scheduler_cqi.add_to_queue(packet)
    
    return jsonify({
        "scheduled_user_id_rl": action_user_id_rl,
        "scheduled_user_id_rr": action_user_id_rr,
        "scheduled_user_id_cqi": action_user_id_cqi
    })

@app.route('/get_statistics/', methods=['GET'])
def get_statistics():
    stats_rl = scheduler_rl.compute_statistics()
    stats_rr = scheduler_rr.compute_statistics()
    stats_cqi = scheduler_cqi.compute_statistics()
    return jsonify({
        "rl": stats_rl,
        "rr": stats_rr,
        "cqi": stats_cqi
    })

@app.route('/get_statistics_history/', methods=['GET'])
def get_statistics_history():
    return jsonify({
        "rl": scheduler_rl.stats_history,
        "rr": scheduler_rr.stats_history,
        "cqi": scheduler_cqi.stats_history
    })

@app.route('/get_traffic_type_counts/', methods=['GET'])
def get_traffic_type_counts():
    return jsonify({
        "rl": scheduler_rl.traffic_type_counts_history,
        "rr": scheduler_rr.traffic_type_counts_history,
        "cqi": scheduler_cqi.traffic_type_counts_history
    })

@app.route('/get_comparative_data', methods=['GET'])
def get_comparative_data():
    return jsonify(comparative_data)

# Serve index.html and app.js
@app.route('/')
def serve_index():
    return send_from_directory('', 'index.html')

@app.route('/app.js')
def serve_js():
    return send_from_directory('', 'app.js')

@app.route('/get_traffic_types/', methods=['GET'])
def get_traffic_types():
    return jsonify(TRAFFIC_TYPES)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5432)