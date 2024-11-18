# qos_comparison.py

import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict

class QoSComparisonAnalytics:
    def __init__(self):
        self.performance_data = {
            'RL': defaultdict(list),
            'RR': defaultdict(list)
        }
        self.comparison_metrics = defaultdict(lambda: {
            'RL': {'total_packets': 0, 'metrics': defaultdict(list)},
            'RR': {'total_packets': 0, 'metrics': defaultdict(list)}
        })
        
    def record_performance(self, qos_mode, stream_id, packet_data, metrics):
        """Record performance data for each QoS mode"""
        timestamp = datetime.now()
        
        # Store raw performance data
        self.performance_data[qos_mode][stream_id].append({
            'timestamp': timestamp,
            'latency': packet_data['latency'],
            'throughput': packet_data['data_rate'],
            'packet_loss': packet_data['packet_loss'],
            'traffic_type': packet_data['traffic_type']
        })
        
        # Update comparison metrics
        stream_metrics = self.comparison_metrics[stream_id]
        stream_metrics[qos_mode]['total_packets'] += 1
        stream_metrics[qos_mode]['metrics']['latency'].append(packet_data['latency'])
        stream_metrics[qos_mode]['metrics']['throughput'].append(packet_data['data_rate'])
        stream_metrics[qos_mode]['metrics']['packet_loss'].append(packet_data['packet_loss'])
        
    def get_comparative_analysis(self, stream_id=None):
        """Generate comparative analysis between RL and RR QoS"""
        if stream_id:
            return self._analyze_single_stream(stream_id)
        return self._analyze_all_streams()
    
    def _analyze_single_stream(self, stream_id):
        metrics = self.comparison_metrics[stream_id]
        
        analysis = {
            'RL': self._calculate_metrics(metrics['RL']),
            'RR': self._calculate_metrics(metrics['RR']),
            'comparison': {}
        }
        
        # Calculate improvements/differences
        for metric in ['avg_latency', 'avg_throughput', 'avg_packet_loss']:
            if analysis['RR'][metric] != 0:
                improvement = ((analysis['RL'][metric] - analysis['RR'][metric]) / analysis['RR'][metric]) * 100
                analysis['comparison'][f'{metric}_improvement'] = improvement
            else:
                analysis['comparison'][f'{metric}_improvement'] = 0
        
        return analysis
    
    def _analyze_all_streams(self):
        all_streams_analysis = {
            'overall': {'RL': {}, 'RR': {}, 'comparison': {}},
            'by_traffic_type': defaultdict(lambda: {'RL': {}, 'RR': {}, 'comparison': {}})
        }
        
        # Analyze each stream
        for stream_id in self.comparison_metrics.keys():
            stream_analysis = self._analyze_single_stream(stream_id)
            
            # Update overall analysis
            self._update_overall_analysis(all_streams_analysis['overall'], stream_analysis)
            
            # Update by traffic type
            traffic_type = self._get_stream_traffic_type(stream_id)
            self._update_overall_analysis(all_streams_analysis['by_traffic_type'][traffic_type], stream_analysis)
        
        return all_streams_analysis
    
    def _calculate_metrics(self, mode_data):
        metrics = mode_data['metrics']
        return {
            'total_packets': mode_data['total_packets'],
            'avg_latency': np.mean(metrics['latency']) if metrics['latency'] else 0,
            'avg_throughput': np.mean(metrics['throughput']) if metrics['throughput'] else 0,
            'avg_packet_loss': np.mean(metrics['packet_loss']) if metrics['packet_loss'] else 0,
            'std_latency': np.std(metrics['latency']) if metrics['latency'] else 0,
            'std_throughput': np.std(metrics['throughput']) if metrics['throughput'] else 0,
            'std_packet_loss': np.std(metrics['packet_loss']) if metrics['packet_loss'] else 0
        }
    
    def _update_overall_analysis(self, target, source):
        for mode in ['RL', 'RR']:
            for metric, value in source[mode].items():
                if metric not in target[mode]:
                    target[mode][metric] = []
                target[mode][metric].append(value)
        
        for metric, value in source['comparison'].items():
            if metric not in target['comparison']:
                target['comparison'][metric] = []
            target['comparison'][metric].append(value)
    
    def _get_stream_traffic_type(self, stream_id):
        if self.performance_data['RL'][stream_id]:
            return self.performance_data['RL'][stream_id][0]['traffic_type']
        if self.performance_data['RR'][stream_id]:
            return self.performance_data['RR'][stream_id][0]['traffic_type']
        return 'unknown'
    
    def generate_comparison_plots(self, stream_id=None, save_path=None):
        """Generate comparison plots between RL and RR QoS"""
        if stream_id:
            self._plot_single_stream(stream_id, save_path)
        else:
            self._plot_all_streams(save_path)
    
    def _plot_single_stream(self, stream_id, save_path=None):
        data = {
            'RL': pd.DataFrame(self.performance_data['RL'][stream_id]),
            'RR': pd.DataFrame(self.performance_data['RR'][stream_id])
        }
        
        fig, axes = plt.subplots(3, 1, figsize=(12, 15))
        
        # Plot latency
        self._plot_metric_comparison(
            axes[0], data, 'latency', 'Latency Comparison',
            'Time', 'Latency (ms)'
        )
        
        # Plot throughput
        self._plot_metric_comparison(
            axes[1], data, 'throughput', 'Throughput Comparison',
            'Time', 'Throughput (Mbps)'
        )
        
        # Plot packet loss
        self._plot_metric_comparison(
            axes[2], data, 'packet_loss', 'Packet Loss Comparison',
            'Time', 'Packet Loss (%)'
        )
        
        plt.tight_layout()
        if save_path:
            plt.savefig(f"{save_path}/stream_{stream_id}_comparison.png")
        plt.close()
    
    def _plot_metric_comparison(self, ax, data, metric, title, xlabel, ylabel):
        for mode, df in data.items():
            ax.plot(df['timestamp'], df[metric], label=f'{mode} QoS')
        
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.legend()
        ax.grid(True)
    
    def generate_report(self, stream_id=None):
        """Generate a detailed comparison report"""
        analysis = self.get_comparative_analysis(stream_id)
        
        report = []
        report.append("QoS Performance Comparison Report")
        report.append("=" * 40)
        
        if stream_id:
            report.append(f"Stream ID: {stream_id}")
            report.extend(self._format_stream_analysis(analysis))
        else:
            report.append("Overall Performance")
            report.extend(self._format_overall_analysis(analysis))
        
        return "\n".join(report)
    
    def _format_stream_analysis(self, analysis):
        lines = []
        
        # Performance Metrics
        lines.append("\nPerformance Metrics:")
        lines.append("-" * 20)
        
        metrics = [
            ('avg_latency', 'Average Latency (ms)'),
            ('avg_throughput', 'Average Throughput (Mbps)'),
            ('avg_packet_loss', 'Average Packet Loss (%)')
        ]
        
        for metric_key, metric_name in metrics:
            lines.append(f"\n{metric_name}:")
            lines.append(f"  RL QoS: {analysis['RL'][metric_key]:.2f}")
            lines.append(f"  RR QoS: {analysis['RR'][metric_key]:.2f}")
            lines.append(f"  Improvement: {analysis['comparison'][f'{metric_key}_improvement']:.2f}%")
        
        return lines
    
    def _format_overall_analysis(self, analysis):
        lines = []
        
        # Overall Performance
        lines.append("\nOverall Performance:")
        lines.append("-" * 20)
        
        for traffic_type, metrics in analysis['by_traffic_type'].items():
            lines.append(f"\nTraffic Type: {traffic_type}")
            lines.extend(self._format_traffic_type_analysis(metrics))
        
        return lines
    
    def _format_traffic_type_analysis(self, metrics):
        lines = []
        
        for mode in ['RL', 'RR']:
            lines.append(f"\n{mode} QoS:")
            for metric, values in metrics[mode].items():
                avg_value = np.mean(values)
                lines.append(f"  {metric}: {avg_value:.2f}")
        
        return lines