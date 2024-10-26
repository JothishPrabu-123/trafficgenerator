import numpy as np
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from tensorflow.keras import layers, models
import json  # For loading simulation data

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
TRAFFIC_LOADS = ["light", "moderate", "heavy"]

app = Flask(__name__)
CORS(app)  # Enable CORS to allow frontend access

class PacketData:
    def __init__(self, data):
        self.user_id = data['user_id']
        self.data_rate = data['data_rate']
        self.latency = data['latency']
        self.packet_loss = data['packet_loss']
        self.user_density = data['user_density']
        self.traffic_load = data['traffic_load']
        self.traffic_type = data.get('traffic_type', '')
        self.cqi = data.get('cqi', 0)
        self.qos_value = None  # Will be set by the CNNScheduler


class RLScheduler:
    def __init__(self, num_users, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.num_users = num_users
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = 0.995
        self.min_epsilon = 0.01
        self.q_table = np.zeros((num_users, num_users))  # Q-table for state-action values
        
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
            return np.argmax(self.q_table[user_id])
        
    def update_q_table(self, user_id, action, reward, next_user_id):
        best_next_action = np.max(self.q_table[next_user_id])
        self.q_table[user_id, action] += self.alpha * (reward + self.gamma * best_next_action - self.q_table[user_id, action])
        
    def add_to_queue(self, data):
        user_id = data.user_id
        action = self.choose_action(user_id)
        reward = -data.latency  # Reward is inversely related to latency
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        next_user_id = (user_id + 1) % self.num_users
        
        # Update statistics
        self.update_statistics(data)

        self.update_q_table(user_id, action, reward, next_user_id)
        return action  # Return action as the user_id to process
    
    def compute_reward(self, data):
        # Define weights for each QoS parameter
        w_latency = 0.5
        w_packet_loss = 0.3
        w_throughput = 0.2
         # Normalize metrics (assuming max values for normalization)
        normalized_latency = data.latency / max_latency
        normalized_packet_loss = data.packet_loss / max_packet_loss
        normalized_throughput = data.data_rate / max_throughput
         # Compute reward
        reward = - (w_latency * normalized_latency + w_packet_loss * normalized_packet_loss - w_throughput * normalized_throughput)
        return reward


        
    def update_statistics(self, data):
        self.total_throughput += data.data_rate
        self.total_latency += data.latency
        self.total_packet_loss += data.packet_loss
        self.count += 1
        
        # Store data based on user density and traffic load
        self.user_density_data[data.user_density].append(data)
        self.traffic_load_data[data.traffic_load].append(data)
        
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
    

class CNNScheduler:
    def __init__(self):
            # Check if a trained model exists
        try:
            self.model = models.load_model('cnn_scheduler_model.h5')
            print("Loaded trained CNN model.")
        except:
            print("Training new CNN model...")
            self.model = self.create_and_train_model()
            # Save the trained model for future use
            self.model.save('cnn_scheduler_model.h5')
        
        # Statistics tracking
        self.total_throughput = 0
        self.total_latency = 0
        self.total_packet_loss = 0
        self.count = 0
        self.user_density_data = {density: [] for density in ["low", "medium", "high"]}
        self.traffic_load_data = {load: [] for load in ["light", "moderate", "heavy"]}
        
        # For real-time statistics
        self.stats_history = []
    
    def create_and_train_model(self):
        # Create and train the CNN model
        X_train, y_train = self.load_simulation_data('simulation_data.json')
        input_shape = (X_train.shape[1], X_train.shape[2])
        
        model = models.Sequential()
        model.add(layers.Conv1D(32, kernel_size=2, activation='relu', input_shape=input_shape))
        model.add(layers.Conv1D(64, kernel_size=2, activation='relu'))
        model.add(layers.Flatten())
        model.add(layers.Dense(64, activation='relu'))
        model.add(layers.Dense(1))  # Output layer for QoS value
        model.compile(optimizer='adam', loss='mse')
        model.fit(X_train, y_train, epochs=10, batch_size=32, verbose=1)
        return model
    
    def load_simulation_data(self, filepath):
        import json
        with open(filepath, 'r') as f:
            data_list = json.load(f)
        
        X = []
        y = []
        for data in data_list:
            features = self.extract_features(data)
            qos_value = self.simulate_qos_value(data)
            X.append(features)
            y.append(qos_value)
        X = np.array(X)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        y = np.array(y)
        return X, y
    
    def generate_training_data(self, num_samples=1000):
        X = []
        y = []
        for _ in range(num_samples):
            data = generate_mock_data()
            features = self.extract_features(data)
            qos_value = self.simulate_qos_value(data)
            X.append(features)
            y.append(qos_value)
        X = np.array(X)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        y = np.array(y)
        return X, y
    
    def extract_features(self, data):
    # Convert categorical variables to numerical representations
        traffic_type_mapping = {key: idx for idx, key in enumerate(TRAFFIC_TYPES.keys())}
        user_density_mapping = {'low': 1, 'medium': 2, 'high': 3}
        traffic_load_mapping = {'light': 1, 'moderate': 2, 'heavy': 3}
        features = [
            data['data_rate'],
            data['latency'],
            data['packet_loss'],
            data['user_id'],
            traffic_type_mapping.get(data['traffic_type'], 0),
            user_density_mapping[data['user_density']],
            traffic_load_mapping[data['traffic_load']],
            data['cqi']
        ]
        return features

    
    def simulate_qos_value(self, data):
        # Simulate QoS value based on data
        qos_value = (data['data_rate'] / (data['latency'] + 1)) * data['cqi'] - data['packet_loss']
        return qos_value

    
    def add_to_queue(self, data):
        # Predict QoS value using the CNN model
        features = np.array(self.extract_features(data)).reshape((1, -1, 1))
        predicted_qos = self.model.predict(features)[0][0]
        data.qos_value = predicted_qos
        
        # Update statistics
        self.update_statistics(data)
        return data.user_id  # Return user_id as the scheduled user
    
    def update_statistics(self, data):
        self.total_throughput += data.data_rate
        self.total_latency += data.latency
        self.total_packet_loss += data.packet_loss
        self.count += 1
        
        # Store data based on user density and traffic load
        self.user_density_data[data.user_density].append(data)
        self.traffic_load_data[data.traffic_load].append(data)
        
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



# Remove the non-RL scheduler and instantiate the CNN scheduler
scheduler_rl = RLScheduler(num_users=20)
scheduler_cnn = CNNScheduler()

@app.route('/process_packet/', methods=['POST'])
def process_packet():
    data = request.get_json()
    packet = PacketData(data)
    
    # Process packet with RL scheduler
    action_user_id_rl = scheduler_rl.add_to_queue(packet)
    # Process packet with CNN-based scheduler
    action_user_id_cnn = scheduler_cnn.add_to_queue(packet)
    
    return jsonify({
        "scheduled_user_id_rl": action_user_id_rl,
        "scheduled_user_id_cnn": action_user_id_cnn
    })

@app.route('/get_statistics/', methods=['GET'])
def get_statistics():
    stats_rl = scheduler_rl.compute_statistics()
    stats_cnn = scheduler_cnn.compute_statistics()
    return jsonify({
        "rl": stats_rl,
        "cnn": stats_cnn
    })

@app.route('/get_statistics_history/', methods=['GET'])
def get_statistics_history():
    return jsonify({
        "rl": scheduler_rl.stats_history,
        "cnn": scheduler_cnn.stats_history
    })



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5432)

