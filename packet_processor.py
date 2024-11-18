# packet_processor.py

from aiohttp import web
import asyncio
import json
import logging
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PacketProcessor:
    def __init__(self):
        self.processed_packets = {}
        self.packet_statistics = {}

    def initialize_stream(self, stream_id):
        if stream_id not in self.processed_packets:
            self.processed_packets[stream_id] = []
            self.packet_statistics[stream_id] = {
                'total_packets': 0,
                'total_data': 0,
                'start_time': datetime.datetime.now(),
                'last_packet_time': None
            }

    async def process_packet(self, packet_data):
        stream_id = packet_data.get('stream_id')
        if not stream_id:
            return {'error': 'Missing stream_id'}

        self.initialize_stream(stream_id)
        
        # Update statistics
        stats = self.packet_statistics[stream_id]
        stats['total_packets'] += 1
        stats['total_data'] += packet_data.get('data_rate', 0)
        current_time = datetime.datetime.now()
        stats['last_packet_time'] = current_time

        # Store processed packet
        processed_packet = {
            'timestamp': current_time.isoformat(),
            'data': packet_data,
            'processing_results': {
                'received_at': current_time.isoformat(),
                'processed_successfully': True,
                'sequence_number': stats['total_packets']
            }
        }
        self.processed_packets[stream_id].append(processed_packet)

        # Keep only last 1000 packets per stream
        if len(self.processed_packets[stream_id]) > 1000:
            self.processed_packets[stream_id].pop(0)

        return {
            'status': 'success',
            'processed_at': current_time.isoformat(),
            'stream_id': stream_id,
            'packet_number': stats['total_packets']
        }

class PacketProcessingServer:
    def __init__(self):
        self.app = web.Application()
        self.processor = PacketProcessor()
        self.setup_routes()

    def setup_routes(self):
        self.app.router.add_post('/process_packet/', self.handle_packet)
        self.app.router.add_get('/statistics/', self.get_statistics)
        self.app.router.add_get('/health/', self.health_check)

    async def handle_packet(self, request):
        try:
            packet_data = await request.json()
            result = await self.processor.process_packet(packet_data)
            return web.json_response(result)
        except Exception as e:
            logger.error(f"Error processing packet: {str(e)}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_statistics(self, request):
        stats = {
            stream_id: {
                'total_packets': stats['total_packets'],
                'total_data': stats['total_data'],
                'uptime': str(datetime.datetime.now() - stats['start_time']),
                'last_packet': str(stats['last_packet_time'])
            }
            for stream_id, stats in self.processor.packet_statistics.items()
        }
        return web.json_response(stats)

    async def health_check(self, request):
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.datetime.now().isoformat(),
            'active_streams': len(self.processor.packet_statistics)
        })

# CORS middleware
@web.middleware
async def cors_middleware(request, handler):
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == '__main__':
    server = PacketProcessingServer()
    app = server.app
    app.middlewares.append(cors_middleware)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Start the server
    logger.info("Starting Packet Processing Server on port 5432...")
    web.run_app(app, host='127.0.0.1', port=5432)