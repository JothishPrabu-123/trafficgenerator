// Network Traffic Generator Application Logic
class NetworkTrafficApp {
    constructor() {
        this.socket = io();
        this.activeStreams = new Map();
        this.initializeSocketListeners();
        this.initializeEventListeners();
        this.qosMode = "RL"; // Default QoS mode
        this.metrics = {};
        this.charts = new Map(); // Store chart instances
    }

    initializeSocketListeners() {
        this.socket.on("packet_status", (data) => {
            this.updateStatusLog(data);
            this.updateStreamCard(data);
            if (data.metrics) {
                this.updateMetrics(data.stream_id, data.metrics);
                this.updateCharts(data.stream_id, data.metrics);
            }
            if (data.qos_mode) {
                this.updateQoSMode(data.qos_mode);
            }
        });
    }

    initializeEventListeners() {
        document.getElementById("add_stream").addEventListener("click", () => this.addNewStream());
        document.getElementById("stop_all").addEventListener("click", () => this.stopAllStreams());
        document.getElementById("active_streams").addEventListener("click", (e) => this.handleStreamControl(e));
        document.getElementById("switch_qos").addEventListener("click", () => this.switchQoSMode());
        document.getElementById("export_metrics").addEventListener("click", () => this.exportMetrics());
    }

    createStreamCard(streamId, trafficType, userDensity) {
        const card = document.createElement('div');
        card.className = 'bg-gray-100 p-4 rounded-lg';
        card.innerHTML = `
            <div class="flex justify-between items-start mb-2">
                <div>
                    <h3 class="font-medium">${trafficType}</h3>
                    <p class="text-sm text-gray-600">Density: ${userDensity}</p>
                </div>
                <button class="stop-stream text-red-600 hover:text-red-800" data-stream-id="${streamId}">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="text-xs text-gray-500">Stream ID: ${streamId.slice(0, 8)}...</div>
            
            <!-- QoS Metrics -->
            <div class="mt-4 space-y-2">
                <div class="text-sm font-medium">QoS Metrics</div>
                <div class="grid grid-cols-2 gap-2 text-sm">
                    <div class="bg-white p-2 rounded">
                        <div class="text-gray-600">Latency</div>
                        <div class="latency-value font-medium">-</div>
                    </div>
                    <div class="bg-white p-2 rounded">
                        <div class="text-gray-600">Throughput</div>
                        <div class="throughput-value font-medium">-</div>
                    </div>
                    <div class="bg-white p-2 rounded">
                        <div class="text-gray-600">Packet Loss</div>
                        <div class="packet-loss-value font-medium">-</div>
                    </div>
                    <div class="bg-white p-2 rounded">
                        <div class="text-gray-600">Jitter</div>
                        <div class="jitter-value font-medium">-</div>
                    </div>
                </div>
            </div>
            
            <!-- Charts -->
            <div class="mt-4">
                <canvas id="chart-${streamId}" class="w-full h-40"></canvas>
            </div>
        `;
        return card;
    }

    async addNewStream() {
        const userDensity = document.getElementById("user_density").value;
        const trafficType = document.getElementById("traffic_type").value;

        try {
            const response = await fetch("/add_traffic_stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_density: userDensity, traffic_type: trafficType })
            });
            const result = await response.json();
            
            if (result.status === "stream_started") {
                const streamCard = this.createStreamCard(result.stream_id, trafficType, userDensity);
                document.getElementById("active_streams").appendChild(streamCard);
                this.initializeChart(result.stream_id);
                this.activeStreams.set(result.stream_id, {
                    trafficType,
                    userDensity,
                    metrics: {
                        latency: [],
                        throughput: [],
                        packetLoss: [],
                        jitter: []
                    }
                });
                this.addStatus(`Started new ${trafficType} stream with ${userDensity} density`);
            }
        } catch (error) {
            this.addStatus(`Error: ${error.message}`);
        }
    }

    initializeChart(streamId) {
        const ctx = document.getElementById(`chart-${streamId}`).getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Latency',
                        borderColor: 'rgb(255, 99, 132)',
                        data: []
                    },
                    {
                        label: 'Throughput',
                        borderColor: 'rgb(75, 192, 192)',
                        data: []
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        this.charts.set(streamId, chart);
    }

    updateMetrics(streamId, metrics) {
        const card = document.querySelector(`[data-stream-id="${streamId}"]`)?.closest('.bg-gray-100');
        if (!card) return;

        // Update metric values
        card.querySelector('.latency-value').textContent = `${metrics.avg_latency.toFixed(2)} ms`;
        card.querySelector('.throughput-value').textContent = `${metrics.avg_throughput.toFixed(2)} Mbps`;
        card.querySelector('.packet-loss-value').textContent = `${metrics.avg_packet_loss.toFixed(2)}%`;
        card.querySelector('.jitter-value').textContent = `${metrics.avg_jitter.toFixed(2)} ms`;

        // Store metrics for export
        if (!this.metrics[streamId]) {
            this.metrics[streamId] = [];
        }
        this.metrics[streamId].push({
            timestamp: new Date().toISOString(),
            ...metrics
        });
    }

    updateCharts(streamId, metrics) {
        const chart = this.charts.get(streamId);
        if (!chart) return;

        const timestamp = new Date().toLocaleTimeString();
        
        // Update chart data
        chart.data.labels.push(timestamp);
        chart.data.datasets[0].data.push(metrics.avg_latency);
        chart.data.datasets[1].data.push(metrics.avg_throughput);

        // Keep only last 20 data points
        if (chart.data.labels.length > 20) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(dataset => dataset.data.shift());
        }

        chart.update();
    }

    async switchQoSMode() {
        try {
            const response = await fetch("/switch_qos_mode", { method: "POST" });
            const result = await response.json();
            this.updateQoSMode(result.mode);
            this.addStatus(`Switched QoS mode to: ${result.mode}`);
        } catch (error) {
            this.addStatus(`Error switching QoS mode: ${error.message}`);
        }
    }

    updateQoSMode(mode) {
        this.qosMode = mode;
        document.getElementById("qos_mode_indicator").textContent = `QoS Mode: ${mode}`;
    }

    exportMetrics() {
        const exportData = {
            timestamp: new Date().toISOString(),
            qosMode: this.qosMode,
            streams: {}
        };

        for (const [streamId, metrics] of Object.entries(this.metrics)) {
            exportData.streams[streamId] = {
                streamData: this.activeStreams.get(streamId),
                metrics: metrics
            };
        }

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `qos-metrics-${new Date().toISOString()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    async stopAllStreams() {
        try {
            await fetch("/stop_all_streams", { method: "POST" });
            document.getElementById("active_streams").innerHTML = '';
            this.activeStreams.clear();
            this.addStatus("All streams stopped");
        } catch (error) {
            this.addStatus(`Error: ${error.message}`);
        }
    }

    async handleStreamControl(event) {
        const stopButton = event.target.closest('.stop-stream');
        if (stopButton) {
            const streamId = stopButton.dataset.streamId;
            try {
                await fetch("/remove_traffic_stream", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ stream_id: streamId })
                });
                stopButton.closest('.bg-gray-100').remove();
                this.activeStreams.delete(streamId);
                this.addStatus(`Stopped stream ${streamId.slice(0, 8)}...`);
            } catch (error) {
                this.addStatus(`Error: ${error.message}`);
            }
        }
    }

    updateStatusLog(data) {
        const statusDiv = document.getElementById("status");
        const newStatus = document.createElement("p");
        newStatus.textContent = `[${data.stream_id.slice(0, 8)}...] ${data.status}: ${JSON.stringify(data.data)}`;
        statusDiv.appendChild(newStatus);
        statusDiv.scrollTop = statusDiv.scrollHeight;
    }

    updateStreamCard(data) {
        if (!data.stream_id) return;

        const card = document.querySelector(`[data-stream-id="${data.stream_id}"]`)?.closest('.bg-gray-100');
        if (!card) return;

        // Update stream statistics
        const streamStats = this.activeStreams.get(data.stream_id)?.stats;
        if (streamStats && data.data) {
            streamStats.packetCount++;
            streamStats.totalLatency += data.data.latency;
            streamStats.totalLoss += data.data.packet_loss;

            // Update UI elements
            card.querySelector('.packet-count').textContent = streamStats.packetCount;
            card.querySelector('.last-rate').textContent = `${data.data.data_rate.toFixed(1)} Mbps`;
            card.querySelector('.avg-latency').textContent = 
                `${(streamStats.totalLatency / streamStats.packetCount).toFixed(1)} ms`;
            card.querySelector('.packet-loss').textContent = 
                `${(streamStats.totalLoss / streamStats.packetCount).toFixed(2)}%`;
        }
    }

    addStatus(message) {
        const statusDiv = document.getElementById("status");
        const newStatus = document.createElement("p");
        newStatus.textContent = message;
        statusDiv.appendChild(newStatus);
        statusDiv.scrollTop = statusDiv.scrollHeight;
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    window.networkApp = new NetworkTrafficApp();
});