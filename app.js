// app.js

const updateInterval = 2000; // Update every 2 seconds

// Initialize datasets
let labels = [];

let throughputDataRL = [];
let latencyDataRL = [];
let packetLossDataRL = [];
let fairnessDataRL = [];

let throughputDataRR = [];
let latencyDataRR = [];
let packetLossDataRR = [];
let fairnessDataRR = [];

let throughputDataCQI = [];
let latencyDataCQI = [];
let packetLossDataCQI = [];
let fairnessDataCQI = [];

// Datasets for Traffic Types
let trafficTypesDataRL = {};
let trafficTypesDataRR = {};
let trafficTypesDataCQI = {};
let trafficTypesChart;

// Get contexts for charts
const throughputCtx = document.getElementById('throughputChart').getContext('2d');
const latencyCtx = document.getElementById('latencyChart').getContext('2d');
const packetLossCtx = document.getElementById('packetLossChart').getContext('2d');
const fairnessCtx = document.getElementById('fairnessChart').getContext('2d');

// Create charts
const throughputChart = new Chart(throughputCtx, {
    type: 'line',
    data: {
        labels: labels,
        datasets: [
            {
                label: 'RL Scheduler',
                data: throughputDataRL,
                borderColor: 'rgba(75, 192, 192, 1)',
                fill: false
            },
            {
                label: 'Round Robin Scheduler',
                data: throughputDataRR,
                borderColor: 'rgba(255, 99, 132, 1)',
                fill: false
            },
            {
                label: 'CQI Scheduler',
                data: throughputDataCQI,
                borderColor: 'rgba(54, 162, 235, 1)',
                fill: false
            }
        ]
    }
});

const latencyChart = new Chart(latencyCtx, {
    type: 'line',
    data: {
        labels: labels,
        datasets: [
            {
                label: 'RL Scheduler',
                data: latencyDataRL,
                borderColor: 'rgba(153, 102, 255, 1)',
                fill: false
            },
            {
                label: 'Round Robin Scheduler',
                data: latencyDataRR,
                borderColor: 'rgba(255, 205, 86, 1)',
                fill: false
            },
            {
                label: 'CQI Scheduler',
                data: latencyDataCQI,
                borderColor: 'rgba(75, 192, 192, 1)',
                fill: false
            }
        ]
    }
});

const packetLossChart = new Chart(packetLossCtx, {
    type: 'line',
    data: {
        labels: labels,
        datasets: [
            {
                label: 'RL Scheduler',
                data: packetLossDataRL,
                borderColor: 'rgba(255, 159, 64, 1)',
                fill: false
            },
            {
                label: 'Round Robin Scheduler',
                data: packetLossDataRR,
                borderColor: 'rgba(54, 162, 235, 1)',
                fill: false
            },
            {
                label: 'CQI Scheduler',
                data: packetLossDataCQI,
                borderColor: 'rgba(201, 203, 207, 1)',
                fill: false
            }
        ]
    }
});

const fairnessChart = new Chart(fairnessCtx, {
    type: 'line',
    data: {
        labels: labels,
        datasets: [
            {
                label: 'RL Scheduler',
                data: fairnessDataRL,
                borderColor: 'rgba(54, 162, 235, 1)',
                fill: false
            },
            {
                label: 'Round Robin Scheduler',
                data: fairnessDataRR,
                borderColor: 'rgba(201, 203, 207, 1)',
                fill: false
            },
            {
                label: 'CQI Scheduler',
                data: fairnessDataCQI,
                borderColor: 'rgba(255, 205, 86, 1)',
                fill: false
            }
        ]
    }
});

// Function to fetch TRAFFIC_TYPES data
async function fetchTrafficTypes() {
    try {
        const response = await fetch('http://127.0.0.1:5432/get_traffic_types/');
        const trafficTypesData = await response.json();

        // Call a function to display the data
        displayTrafficTypes(trafficTypesData);
    } catch (error) {
        console.error('Error fetching traffic types:', error);
    }
}

// Function to display TRAFFIC_TYPES data in the HTML
function displayTrafficTypes(data) {
    const trafficTypesContainer = document.getElementById('trafficTypesContainer');

    // Clear any existing content
    trafficTypesContainer.innerHTML = '';

    // Create a table or list to display the data
    const table = document.createElement('table');
    table.className = 'min-w-full bg-white';

    // Table header
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th class="px-4 py-2">Traffic Type</th>
            <th class="px-4 py-2">Data Rate (Mbps)</th>
            <th class="px-4 py-2">Latency (ms)</th>
        </tr>
    `;
    table.appendChild(thead);

    // Table body
    const tbody = document.createElement('tbody');

    for (const [trafficType, characteristics] of Object.entries(data)) {
        const row = document.createElement('tr');

        row.innerHTML = `
            <td class="border px-4 py-2">${trafficType}</td>
            <td class="border px-4 py-2">${characteristics.data_rate}</td>
            <td class="border px-4 py-2">${characteristics.latency}</td>
        `;
        tbody.appendChild(row);
    }

    table.appendChild(tbody);
    trafficTypesContainer.appendChild(table);
}

// Call fetchTrafficTypes when the page loads
window.addEventListener('load', () => {
    setInterval(fetchTrafficTypeCounts, updateInterval);

    // Existing code to fetch and update charts
    setInterval(fetchData, updateInterval);
});

// Function to fetch data from the backend
async function fetchData() {
    try {
        const response = await fetch('http://127.0.0.1:5432/get_statistics/');
        const data = await response.json();
        const statsRL = data.rl;
        const statsRR = data.rr;
        const statsCQI = data.cqi;

        const currentTime = new Date().toLocaleTimeString();

        // Update datasets
        labels.push(currentTime);

        throughputDataRL.push(statsRL.throughput);
        latencyDataRL.push(statsRL.average_latency);
        packetLossDataRL.push(statsRL.average_packet_loss);
        fairnessDataRL.push(statsRL.fairness_index);

        throughputDataRR.push(statsRR.throughput);
        latencyDataRR.push(statsRR.average_latency);
        packetLossDataRR.push(statsRR.average_packet_loss);
        fairnessDataRR.push(statsRR.fairness_index);

        throughputDataCQI.push(statsCQI.throughput);
        latencyDataCQI.push(statsCQI.average_latency);
        packetLossDataCQI.push(statsCQI.average_packet_loss);
        fairnessDataCQI.push(statsCQI.fairness_index);

        // Keep only the last 20 data points
        if (labels.length > 20) {
            labels.shift();

            throughputDataRL.shift();
            latencyDataRL.shift();
            packetLossDataRL.shift();
            fairnessDataRL.shift();

            throughputDataRR.shift();
            latencyDataRR.shift();
            packetLossDataRR.shift();
            fairnessDataRR.shift();

            throughputDataCQI.shift();
            latencyDataCQI.shift();
            packetLossDataCQI.shift();
            fairnessDataCQI.shift();
        }

        // Update charts
        throughputChart.update();
        latencyChart.update();
        packetLossChart.update();
        fairnessChart.update();

    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// Function to fetch traffic type counts
async function fetchTrafficTypeCounts() {
    try {
        const response = await fetch('http://127.0.0.1:5432/get_traffic_type_counts/');
        const data = await response.json();

        // Process data for each scheduler
        processTrafficTypeCounts('RL Scheduler', data.rl, trafficTypesDataRL);
        processTrafficTypeCounts('Round Robin Scheduler', data.rr, trafficTypesDataRR);
        processTrafficTypeCounts('CQI Scheduler', data.cqi, trafficTypesDataCQI);

        // Update the traffic types chart
        updateTrafficTypesChart();

    } catch (error) {
        console.error('Error fetching traffic type counts:', error);
    }
}

function processTrafficTypeCounts(schedulerName, schedulerData, trafficTypesData) {
    // Clear existing data
    trafficTypesData.labels = [];
    trafficTypesData.datasets = {};

    // Collect all traffic types
    const allTrafficTypes = new Set();
    schedulerData.forEach(entry => {
        Object.keys(entry.counts).forEach(trafficType => {
            allTrafficTypes.add(trafficType);
        });
    });

    // Initialize datasets for each traffic type
    allTrafficTypes.forEach(trafficType => {
        if (!trafficTypesData.datasets[trafficType]) {
            trafficTypesData.datasets[trafficType] = [];
        }
    });

    // Process data
    schedulerData.forEach(entry => {
        const timestamp = new Date(entry.timestamp * 1000).toLocaleTimeString();
        trafficTypesData.labels.push(timestamp);

        allTrafficTypes.forEach(trafficType => {
            const count = entry.counts[trafficType] || 0;
            trafficTypesData.datasets[trafficType].push(count);
        });
    });
}

function updateTrafficTypesChart() {
    const ctx = document.getElementById('trafficTypesChart').getContext('2d');

    // If the chart already exists, destroy it
    if (trafficTypesChart) {
        trafficTypesChart.destroy();
    }

    // Prepare data for the chart
    const datasets = [];
    const colors = [
        'rgba(75, 192, 192, 1)',
        'rgba(255, 99, 132, 1)',
        'rgba(54, 162, 235, 1)',
        'rgba(255, 205, 86, 1)',
        'rgba(153, 102, 255, 1)',
        'rgba(201, 203, 207, 1)'
    ];
    

    let colorIndex = 0;
    for (const [trafficType, data] of Object.entries(trafficTypesDataRL.datasets)) {
        datasets.push({
            label: trafficType,
            data: data,
            borderColor: colors[colorIndex % colors.length],
            backgroundColor: colors[colorIndex % colors.length],
            fill: false,
            tension: 0.1  // Smoothes the lines; adjust as needed
        });
        colorIndex++;
    }

    // Create the chart
    trafficTypesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: trafficTypesDataRL.labels,
            datasets: datasets
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: 'Traffic Types Per Second (RL Scheduler)'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top'
                }
            },
            responsive: true,
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Number of Packets'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}



// Set interval to update charts
setInterval(fetchData, updateInterval);
