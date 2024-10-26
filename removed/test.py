import numpy as np
import tensorflow as tf
from tensorflow.keras import models
import json

# Define constants for feature extraction
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

def extract_features(data):
    # Convert categorical variables to numerical representations
    traffic_type_mapping = {key: idx for idx, key in enumerate(TRAFFIC_TYPES.keys())}
    user_density_mapping = {'low': 1, 'medium': 2, 'high': 3}
    traffic_load_mapping = {'light': 1, 'moderate': 2, 'heavy': 3}

    features = [
        data['data_rate'],
        data['latency'],
        data['packet_loss'],
        data['user_id'],
        traffic_type_mapping.get(data.get('traffic_type', ''), 0),
        user_density_mapping[data['user_density']],
        traffic_load_mapping[data['traffic_load']],
        data.get('cqi', 0)
    ]
    return features

# Load simulation data
with open('simulation_data.json', 'r') as f:
    data_list = json.load(f)

# Load the trained CNN model
model = models.load_model('cnn_scheduler_model.h5', compile=False)
model.compile(optimizer='adam', loss=tf.keras.losses.MeanSquaredError())


# Process data and print CNN-based values
print("CNN-Based Predicted QoS Values:")
print("--------------------------------")

for i, data in enumerate(data_list):
    features = np.array(extract_features(data)).reshape((1, -1, 1))
    predicted_qos = model.predict(features)[0][0]
    print(f"Data Point {i+1}: User ID = {data['user_id']}, Predicted QoS = {predicted_qos:.4f}")

# Optionally, limit the number of data points processed
# Uncomment the following lines to process only the first 100 data points
# for i, data in enumerate(data_list[:100]):
#     # Processing code as above
