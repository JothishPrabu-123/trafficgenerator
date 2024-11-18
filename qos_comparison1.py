import numpy as np
from collections import defaultdict
from datetime import datetime
import json
import os

class QoSComparisonAnalytics:
    def __init__(self):
        self.metrics = {
            'RL': defaultdict(lambda: defaultdict(list)),
            'RR': defaultdict(lambda: defaultdict(list))
        }
        
        self.performance_stats = {
            'RL': defaultdict(lambda: {
                'total_packets': 0,
                'success_packets': 0,
                'latency': [],
                'throughput': [],
                'packet_loss': [],
                'jitter': [],
                'start_time': None,
                'traffic_type': None
            }),
            'RR': defaultdict(lambda: {
                'total_packets': 0,
                'success_packets': 0,
                'latency': [],
                'throughput': [],
                'packet_loss': [],
                'jitter': [],
                'start_time': None,
                'traffic_type': None
            })
        }
        
        self.traffic_types = set()
        self.comparison_history = []
        self.window_size = 100  # Rolling window size for metrics

    def record_metrics(self, qos_mode, stream_id, packet_data, metrics):
        """Record metrics for a specific stream and QoS mode"""
        # Initialize start time if not set
        if self.performance_stats[qos_mode][stream_id]['start_time'] is None:
            self.performance_stats[qos_mode][stream_id]['start_time'] = datetime.now()
            self.performance_stats[qos_mode][stream_id]['traffic_type'] = packet_data['traffic_type']

        # Update basic metrics
        metrics_data = self.metrics[qos_mode][stream_id]
        metrics_data['latency'].append(packet_data['latency'])
        metrics_data['throughput'].append(packet_data['data_rate'])
        metrics_data['packet_loss'].append(packet_data['packet_loss'])

        # Keep only window_size recent measurements
        for key in ['latency', 'throughput', 'packet_loss']:
            if len(metrics_data[key]) > self.window_size:
                metrics_data[key] = metrics_data[key][-self.window_size:]

        # Update performance statistics
        stats = self.performance_stats[qos_mode][stream_id]
        stats['total_packets'] += 1
        if packet_data['packet_loss'] < 1:  # Consider packet successful if loss is less than 1%
            stats['success_packets'] += 1
        
        # Update rolling metrics
        for key in ['latency', 'throughput', 'packet_loss']:
            stats[key].append(packet_data[key])
            if len(stats[key]) > self.window_size:
                stats[key] = stats[key][-self.window_size:]

        # Calculate and update jitter
        if len(stats['latency']) > 1:
            jitter = abs(stats['latency'][-1] - stats['latency'][-2])
            stats['jitter'].append(jitter)
            if len(stats['jitter']) > self.window_size:
                stats['jitter'] = stats['jitter'][-self.window_size:]

        # Track traffic type
        self.traffic_types.add(packet_data['traffic_type'])

        # Record comparison snapshot
        self._record_comparison_snapshot(stream_id, qos_mode, packet_data)

    def _record_comparison_snapshot(self, stream_id, qos_mode, packet_data):
        """Record a snapshot of performance metrics for comparison"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'stream_id': stream_id,
            'qos_mode': qos_mode,
            'traffic_type': packet_data['traffic_type'],
            'metrics': {
                'latency': packet_data['latency'],
                'throughput': packet_data['data_rate'],
                'packet_loss': packet_data['packet_loss']
            }
        }
        self.comparison_history.append(snapshot)
        
        # Keep only last 1000 snapshots
        if len(self.comparison_history) > 1000:
            self.comparison_history = self.comparison_history[-1000:]

    def get_stream_comparison(self, stream_id):
        """Get detailed comparison metrics for a specific stream"""
        comparison = {}
        
        for mode in ['RL', 'RR']:
            if stream_id in self.metrics[mode]:
                metrics = self.metrics[mode][stream_id]
                stats = self.performance_stats[mode][stream_id]
                
                comparison[mode] = {
                    'current_metrics': {
                        'avg_latency': np.mean(metrics['latency']) if metrics['latency'] else 0,
                        'avg_throughput': np.mean(metrics['throughput']) if metrics['throughput'] else 0,
                        'avg_packet_loss': np.mean(metrics['packet_loss']) if metrics['packet_loss'] else 0,
                        'avg_jitter': np.mean(stats['jitter']) if stats['jitter'] else 0
                    },
                    'performance_stats': {
                        'total_packets': stats['total_packets'],
                        'success_rate': (stats['success_packets'] / stats['total_packets'] * 100) if stats['total_packets'] > 0 else 0,
                        'uptime': str(datetime.now() - stats['start_time']) if stats['start_time'] else '0',
                        'traffic_type': stats['traffic_type']
                    },
                    'stability_metrics': {
                        'latency_variance': np.var(metrics['latency']) if metrics['latency'] else 0,
                        'throughput_stability': self._calculate_stability(metrics['throughput']),
                        'packet_loss_trend': self._calculate_trend(metrics['packet_loss'])
                    }
                }

        # Calculate improvements if both modes have data
        if 'RL' in comparison and 'RR' in comparison:
            comparison['improvements'] = self._calculate_improvements(
                comparison['RL']['current_metrics'],
                comparison['RR']['current_metrics']
            )
            
        return comparison

    def get_overall_comparison(self):
        """Get comprehensive QoS performance comparison"""
        overall_stats = {
            'RL': self._calculate_overall_stats('RL'),
            'RR': self._calculate_overall_stats('RR'),
            'by_traffic_type': self._calculate_traffic_type_stats(),
            'time_series_analysis': self._analyze_time_series(),
            'performance_summary': self._generate_performance_summary()
        }
        
        # Calculate overall improvements
        if overall_stats['RL'] and overall_stats['RR']:
            overall_stats['improvements'] = self._calculate_improvements(
                overall_stats['RL'],
                overall_stats['RR']
            )
        
        return overall_stats

    def _calculate_stability(self, values):
        """Calculate stability score based on value variations"""
        if not values:
            return 0
        mean = np.mean(values)
        if mean == 0:
            return 0
        return 1 - min(1, np.std(values) / mean)

    def _calculate_trend(self, values):
        """Calculate trend direction and strength"""
        if len(values) < 2:
            return 0
        diffs = np.diff(values)
        return np.mean(diffs)

    def _calculate_improvements(self, rl_metrics, rr_metrics):
        """Calculate improvement percentages between RL and RR"""
        improvements = {}
        
        for metric in ['avg_latency', 'avg_packet_loss', 'avg_jitter']:
            if rr_metrics[metric] != 0:
                improvements[metric] = (
                    (rr_metrics[metric] - rl_metrics[metric]) / rr_metrics[metric] * 100
                )
            else:
                improvements[metric] = 0

        # For throughput, higher is better
        if rr_metrics['avg_throughput'] != 0:
            improvements['avg_throughput'] = (
                (rl_metrics['avg_throughput'] - rr_metrics['avg_throughput']) 
                / rr_metrics['avg_throughput'] * 100
            )
        else:
            improvements['avg_throughput'] = 0

        # Calculate overall improvement
        improvements['overall'] = np.mean([
            improvements['avg_throughput'],
            -improvements['avg_latency'],  # Negative because lower latency is better
            -improvements['avg_packet_loss'],  # Negative because lower packet loss is better
            -improvements['avg_jitter']  # Negative because lower jitter is better
        ])

        return improvements

    def _analyze_time_series(self):
        """Analyze performance trends over time"""
        analysis = {
            'RL': {'latency': [], 'throughput': [], 'packet_loss': []},
            'RR': {'latency': [], 'throughput': [], 'packet_loss': []}
        }
        
        for snapshot in self.comparison_history:
            mode = snapshot['qos_mode']
            metrics = snapshot['metrics']
            
            for key in ['latency', 'throughput', 'packet_loss']:
                analysis[mode][key].append(metrics[key])
        
        return analysis

    def _generate_performance_summary(self):
        """Generate a summary of overall performance"""
        rl_stats = self._calculate_overall_stats('RL')
        rr_stats = self._calculate_overall_stats('RR')
        
        return {
            'total_packets_processed': sum(
                stats['total_packets'] 
                for mode in self.performance_stats.values() 
                for stats in mode.values()
            ),
            'active_streams': len(set(
                stream_id 
                for mode in self.performance_stats.values() 
                for stream_id in mode.keys()
            )),
            'average_improvement': self._calculate_improvements(rl_stats, rr_stats)['overall']
            if rl_stats and rr_stats else 0
        }

    def export_metrics(self, filename=None):
        """Export all metrics and analysis to a JSON file"""
        if filename is None:
            if not os.path.exists('metrics'):
                os.makedirs('metrics')
            filename = f"metrics/qos_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_comparison': self.get_overall_comparison(),
            'stream_metrics': {
                stream_id: self.get_stream_comparison(stream_id)
                for stream_id in set(
                    list(self.metrics['RL'].keys()) + 
                    list(self.metrics['RR'].keys())
                )
            },
            'traffic_type_analysis': self._calculate_traffic_type_stats(),
            'comparison_history': self.comparison_history[-100:]  # Last 100 snapshots
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        return filename

    def _calculate_overall_stats(self, mode):
        """Calculate overall statistics for a QoS mode"""
        stats = defaultdict(list)
        
        for stream_metrics in self.performance_stats[mode].values():
            for key in ['latency', 'throughput', 'packet_loss', 'jitter']:
                stats[key].extend(stream_metrics[key])
        
        if not any(stats.values()):
            return None
            
        return {
            'avg_latency': np.mean(stats['latency']) if stats['latency'] else 0,
            'avg_throughput': np.mean(stats['throughput']) if stats['throughput'] else 0,
            'avg_packet_loss': np.mean(stats['packet_loss']) if stats['packet_loss'] else 0,
            'avg_jitter': np.mean(stats['jitter']) if stats['jitter'] else 0
        }

    def _calculate_traffic_type_stats(self):
        """Calculate statistics grouped by traffic type"""
        traffic_stats = {}
        
        for traffic_type in self.traffic_types:
            traffic_stats[traffic_type] = {
                'RL': self._calculate_traffic_type_mode_stats('RL', traffic_type),
                'RR': self._calculate_traffic_type_mode_stats('RR', traffic_type)
            }
            
            # Calculate improvements for this traffic type
            if traffic_stats[traffic_type]['RL'] and traffic_stats[traffic_type]['RR']:
                traffic_stats[traffic_type]['improvements'] = self._calculate_improvements(
                    traffic_stats[traffic_type]['RL'],
                    traffic_stats[traffic_type]['RR']
                )
        
        return traffic_stats

    def _calculate_traffic_type_mode_stats(self, mode, traffic_type):
        """Calculate statistics for a specific traffic type and QoS mode"""
        relevant_streams = [
            stream_id for stream_id, stats in self.performance_stats[mode].items()
            if stats['traffic_type'] == traffic_type
        ]
        
        if not relevant_streams:
            return None
            
        combined_stats = defaultdict(list)
        for stream_id in relevant_streams:
            stats = self.performance_stats[mode][stream_id]
            for key in ['latency', 'throughput', 'packet_loss', 'jitter']:
                combined_stats[key].extend(stats[key])
        
        return {
            'avg_latency': np.mean(combined_stats['latency']) if combined_stats['latency'] else 0,
            'avg_throughput': np.mean(combined_stats['throughput']) if combined_stats['throughput'] else 0,
            'avg_packet_loss': np.mean(combined_stats['packet_loss']) if combined_stats['packet_loss'] else 0,
            'avg_jitter': np.mean(combined_stats['jitter']) if combined_stats['jitter'] else 0
        }