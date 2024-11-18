Certainly! Below are the `requirements.txt` and a `README.md` file to help you set up and run your code.

<img width="1346" alt="Screenshot 2024-10-26 at 10 48 56 AM" src="https://github.com/user-attachments/assets/e7be9675-fd4c-4ca8-a241-8e6bff05a801">
---

**`requirements.txt`**

```text
Flask
flask-cors
numpy
aiohttp
```

---

**`README.md`**

# RL Scheduler Dashboard Setup Guide

This guide will help you set up and run the RL Scheduler Dashboard, which includes a Flask backend, a data generator, and a frontend dashboard to visualize the performance of different network schedulers.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [File Structure](#file-structure)
- [Schedulers Implemented](#schedulers-implemented)
- [Technologies Used](#technologies-used)
- [Troubleshooting](#troubleshooting)
- [Customization](#customization)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

- **Python 3.7** or higher installed on your system.
- A modern web browser (e.g., Chrome, Firefox, Edge).
- **Git** (optional, for cloning the repository).

## Installation

1. **Clone the Repository**

   Clone the repository containing the code to your local machine.

   ```bash
   git clone https://github.com/VishalVrk/trafficgenerator
   ```


2. **Navigate to the Project Directory**

   ```bash
   cd trafficgenerator
   ```

3. **Create a Virtual Environment**

   It's recommended to create a virtual environment to manage your Python dependencies.

   ```bash
   python3 -m venv venv
   ```

4. **Activate the Virtual Environment**

   - On macOS/Linux:

     ```bash
     source venv/bin/activate
     ```

   - On Windows:

     ```bash
     venv\Scripts\activate
     ```

5. **Install Dependencies**

   Use `pip` to install the required Python packages from the `requirements.txt` file.

   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### 1. Start the Flask Backend Server

Run the `app.py` file to start the Flask backend server.

```bash
python app.py
```

The server will start running on `http://127.0.0.1:5432/`.

### 2. Run the Data Generator

In a new terminal window (while keeping the Flask server running), run the `data_generator.py` script to start generating mock network data.

```bash
python data_generator.py
```

This script sends simulated network packets to the backend server for processing.

### 3. Access the Dashboard

Open your web browser and navigate to:

```
http://127.0.0.1:5432/
```

You should see the RL Scheduler Dashboard with charts displaying real-time data.

## File Structure

- **`app.py`**: The Flask backend application that processes incoming packet data, runs the schedulers, and serves the frontend files.
- **`data_generator.py`**: Generates mock network packet data and sends it to the backend server.
- **`index.html`**: The main HTML file for the frontend dashboard.
- **`app.js`**: The frontend JavaScript file that fetches data from the backend and updates the charts.
- **`requirements.txt`**: Lists all the Python dependencies required to run the application.

## Schedulers Implemented

The application includes the following schedulers for comparison:

1. **Reinforcement Learning (RL) Scheduler**: Learns optimal scheduling policies based on network conditions and QoS parameters.
2. **Round Robin Scheduler**: Cycles through users in order, providing equal opportunity without considering network conditions.
3. **CQI-based Scheduler**: Prioritizes users based on their Channel Quality Indicator (CQI) values, favoring users with better channel conditions.

## Technologies Used

- **Python**: Backend server and data generator.
- **Flask**: Web framework for the backend server.
- **Flask-CORS**: Handles Cross-Origin Resource Sharing (CORS) to allow communication between frontend and backend.
- **NumPy**: Used for numerical computations in the schedulers.
- **aiohttp**: Asynchronous HTTP client used in the data generator.
- **JavaScript (ES6)**: Frontend logic for fetching data and updating charts.
- **Chart.js**: Library used for creating responsive charts in the frontend.
- **Tailwind CSS**: Utility-first CSS framework used for styling the frontend.

## Troubleshooting

- **Port Already in Use Error**: If port `5432` is already in use, change the port number in both `app.py` and `data_generator.py` to an available port.
  - In `app.py`:

    ```python
    if __name__ == '__main__':
        app.run(debug=True, host='0.0.0.0', port=<new_port_number>)
    ```

  - In `data_generator.py`:

    ```python
    async with session.post("http://127.0.0.1:<new_port_number>/process_packet/", json=data) as response:
    ```

- **CORS Errors**: Ensure that `flask-cors` is properly installed and `CORS(app)` is included in `app.py`.

- **Module Not Found Errors**: Ensure all dependencies are installed by running `pip install -r requirements.txt` in your virtual environment.

- **Charts Not Displaying**: Check the browser console for errors. Ensure that `app.js` is correctly included in `index.html` and that the backend server is running.

## Customization

- **Adding New Schedulers**: You can implement additional schedulers by creating new classes in `app.py` and updating the frontend to include them.

- **Modifying Traffic Types**: Update the `TRAFFIC_TYPES` dictionary in `app.py` and adjust the data generator accordingly.

- **Styling the Dashboard**: Customize the frontend by modifying `index.html` and `app.js`, and adjusting the Tailwind CSS classes.

## Contributing

If you'd like to contribute to this project, please fork the repository and submit a pull request. Contributions are welcome!

## License

This project is licensed under the MIT License.

---
