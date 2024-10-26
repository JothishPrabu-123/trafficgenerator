import numpy as np
import random

class RLScheduler:
    def __init__(self, num_users, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.num_users = num_users
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = np.zeros((num_users, num_users))  # Q-table for state-action values
        
        # To keep track of statistics
        self.total_throughput = 0
        self.total_latency = 0
        self.total_packet_loss = 0
        self.count = 0  # Number of processed packets
        self.user_density_data = {density: [] for density in ["low", "medium", "high"]}
        self.traffic_load_data = {load: [] for load in ["light", "moderate", "heavy"]}

    def choose_action(self, user_id):
        if random.uniform(0, 1) < self.epsilon:
            return random.randint(0, self.num_users - 1)
        else:
            return np.argmax(self.q_table[user_id])
    
    def update_q_table(self, user_id, action, reward, next_user_id):
        best_next_action = np.max(self.q_table[next_user_id])
        self.q_table[user_id, action] += self.alpha * (reward + self.gamma * best_next_action - self.q_table[user_id, action])
    
    def add_to_queue(self, data):
        user_id = data['user_id']
        action = self.choose_action(user_id)
        reward = -data['latency']  # Reward is inversely related to latency
        next_user_id = (user_id + 1) % self.num_users
        
        # Update statistics
        self.update_statistics(data)

        self.update_q_table(user_id, action, reward, next_user_id)
        return user_id  # Return user_id as the action to process
    
    def update_statistics(self, data):
        self.total_throughput += data['data_rate']
        self.total_latency += data['latency']
        self.total_packet_loss += data['packet_loss']
        self.count += 1
        
        # Store data based on user density and traffic load
        self.user_density_data[data['user_density']].append(data)
        self.traffic_load_data[data['traffic_load']].append(data)
    
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

        # Fairness index can be computed based on the max/min throughput
        fairness_index = (min([len(self.user_density_data[key]) for key in self.user_density_data]) /
                          (max([len(self.user_density_data[key]) for key in self.user_density_data]) or 1))

        return {
            "throughput": average_throughput,
            "average_latency": average_latency,
            "average_packet_loss": average_packet_loss,
            "fairness_index": fairness_index
        }
