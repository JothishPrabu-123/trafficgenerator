# qos_manager.py

import numpy as np
from collections import deque
import random

class RLQoSManager:
    def __init__(self, n_states=8, n_actions=3, learning_rate=0.1, gamma=0.95):
        self.n_states = n_states  # States based on queue length and priority
        self.n_actions = n_actions  # Actions: high, medium, low bandwidth allocation
        self.q_table = np.zeros((n_states, n_actions))
        self.lr = learning_rate
        self.gamma = gamma
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01
        
    def get_state(self, queue_length, packet_priority, packet_delay):
    # Normalize and discretize state parameters
        queue_state = min(3, queue_length // 5)  # 0-3 based on queue length
        priority_state = min(1, packet_priority)  # 0-1 based on priority
        delay_state = min(1, int(packet_delay > 50))  # 0-1 based on delay threshold
        
        # Ensure the state index is within bounds
        state = queue_state * 4 + priority_state * 2 + delay_state
        return min(state, self.n_states - 1)  # Cap the state to max allowed

    
    def get_action(self, state):
        if random.random() < self.epsilon:
            return random.randint(0, self.n_actions - 1)
        return np.argmax(self.q_table[state])
    
    def update(self, state, action, reward, next_state):
        old_value = self.q_table[state, action]
        next_max = np.max(self.q_table[next_state])
        new_value = (1 - self.lr) * old_value + self.lr * (reward + self.gamma * next_max)
        self.q_table[state, action] = new_value
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

class RoundRobinQoS:
    def __init__(self, time_slice=5):
        self.queue = deque()
        self.time_slice = time_slice
        self.current_slice = 0
        self.current_stream = None
    
    def add_stream(self, stream_id):
        if stream_id not in self.queue:
            self.queue.append(stream_id)
    
    def remove_stream(self, stream_id):
        if stream_id in self.queue:
            self.queue.remove(stream_id)
            if self.current_stream == stream_id:
                self.current_stream = None
                self.current_slice = 0
    
    def get_next_stream(self):
        if not self.queue:
            return None
            
        if self.current_slice >= self.time_slice or self.current_stream is None:
            self.current_stream = self.queue[0]
            self.queue.rotate(-1)
            self.current_slice = 0
            
        self.current_slice += 1
        return self.current_stream

class QoSMetricsCollector:
    def __init__(self):
        self.metrics = {}
        
    def initialize_stream(self, stream_id):
        self.metrics[stream_id] = {
            'latency': [],
            'throughput': [],
            'packet_loss': [],
            'jitter': [],
            'last_packet_time': None
        }
    
    def update_metrics(self, stream_id, packet_data):
        if stream_id not in self.metrics:
            self.initialize_stream(stream_id)
            
        metrics = self.metrics[stream_id]
        
        # Update latency
        metrics['latency'].append(packet_data['latency'])
        
        # Update throughput
        metrics['throughput'].append(packet_data['data_rate'])
        
        # Update packet loss
        metrics['packet_loss'].append(packet_data['packet_loss'])
        
        # Calculate and update jitter
        current_time = packet_data.get('timestamp', 0)
        if metrics['last_packet_time'] is not None:
            jitter = abs(current_time - metrics['last_packet_time'])
            metrics['jitter'].append(jitter)
        metrics['last_packet_time'] = current_time
    
    def get_stream_metrics(self, stream_id):
        if stream_id not in self.metrics:
            return None
            
        m = self.metrics[stream_id]
        return {
            'avg_latency': np.mean(m['latency']) if m['latency'] else 0,
            'avg_throughput': np.mean(m['throughput']) if m['throughput'] else 0,
            'avg_packet_loss': np.mean(m['packet_loss']) if m['packet_loss'] else 0,
            'avg_jitter': np.mean(m['jitter']) if m['jitter'] else 0
        }
    
    def clear_metrics(self, stream_id):
        if stream_id in self.metrics:
            del self.metrics[stream_id]

class QoSManager:
    def __init__(self):
        self.rl_qos = RLQoSManager()
        self.rr_qos = RoundRobinQoS()
        self.metrics_collector = QoSMetricsCollector()
        self.active_streams = {}
        self.qos_mode = "RL"  # or "RR" for Round Robin
        
    def add_stream(self, stream_id, traffic_type, user_density):
        self.active_streams[stream_id] = {
            'traffic_type': traffic_type,
            'user_density': user_density,
            'queue': deque(maxlen=100),
            'priority': self._get_traffic_priority(traffic_type)
        }
        self.rr_qos.add_stream(stream_id)
        self.metrics_collector.initialize_stream(stream_id)
    
    def remove_stream(self, stream_id):
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
            self.rr_qos.remove_stream(stream_id)
            self.metrics_collector.clear_metrics(stream_id)
    
    def _get_traffic_priority(self, traffic_type):
        priority_map = {
            "Voice Call": 3,
            "Video Call": 3,
            "YouTube": 2,
            "Instagram": 1,
            "WhatsApp": 1,
            "Text Message": 0
        }
        return priority_map.get(traffic_type, 1)
    
    def process_packet(self, stream_id, packet_data):
        if stream_id not in self.active_streams:
            return packet_data
            
        stream = self.active_streams[stream_id]
        stream['queue'].append(packet_data)
        
        if self.qos_mode == "RL":
            state = self.rl_qos.get_state(
                len(stream['queue']),
                stream['priority'],
                packet_data['latency']
            )
            action = self.rl_qos.get_action(state)
            
            # Apply QoS based on RL action
            modified_packet = self._apply_rl_qos(packet_data, action)
            
            # Calculate reward based on QoS metrics
            reward = self._calculate_reward(modified_packet, stream['priority'])
            
            # Update RL model
            next_state = self.rl_qos.get_state(
                len(stream['queue']),
                stream['priority'],
                modified_packet['latency']
            )
            self.rl_qos.update(state, action, reward, next_state)
            
        else:  # Round Robin
            next_stream = self.rr_qos.get_next_stream()
            modified_packet = self._apply_rr_qos(packet_data, stream_id == next_stream)
        
        # Collect metrics
        self.metrics_collector.update_metrics(stream_id, modified_packet)
        return modified_packet
    
    def _apply_rl_qos(self, packet_data, action):
        # Modify packet characteristics based on RL action
        bandwidth_multipliers = [1.2, 1.0, 0.8]  # high, medium, low
        modified_packet = packet_data.copy()
        
        # Adjust data rate based on action
        modified_packet['data_rate'] *= bandwidth_multipliers[action]
        
        # Adjust latency inversely to bandwidth allocation
        modified_packet['latency'] *= (2 - bandwidth_multipliers[action])
        
        return modified_packet
    
    def _apply_rr_qos(self, packet_data, is_current):
        modified_packet = packet_data.copy()
        
        # If this stream is currently selected, give it full bandwidth
        if is_current:
            modified_packet['data_rate'] *= 1.2
            modified_packet['latency'] *= 0.8
        else:
            modified_packet['data_rate'] *= 0.8
            modified_packet['latency'] *= 1.2
        
        return modified_packet
    
    def _calculate_reward(self, packet_data, priority):
        # Calculate reward based on QoS metrics and priority
        latency_score = max(0, 1 - packet_data['latency'] / 100)
        throughput_score = min(1, packet_data['data_rate'] / 50)
        packet_loss_score = max(0, 1 - packet_data['packet_loss'] / 5)
        
        # Weight the scores based on priority
        priority_multiplier = 1 + (priority * 0.5)
        return priority_multiplier * (latency_score + throughput_score + packet_loss_score) / 3
    
    def get_metrics(self, stream_id):
        return self.metrics_collector.get_stream_metrics(stream_id)
    
    def switch_qos_mode(self):
        self.qos_mode = "RR" if self.qos_mode == "RL" else "RL"
        return self.qos_mode