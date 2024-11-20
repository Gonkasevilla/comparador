from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from perplexity_analyzer import ProductAnalyzer
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='public')
CORS(app)

# Health check para Railway
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200

# Serve static files
@app.route('/')
def serve_index():
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        logger.error(f"Error serving index: {str(e)}")
        return jsonify({'error': 'Error serving index page'}), 500

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory(app.static_folder, path)
    except Exception as e:
        logger.error(f"Error serving static file {path}: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

# API endpoint
@app.route('/api/compare', methods=['POST'])
def compare_products():
    try:
        logger.info("Received comparison request")
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        urls = request.json.get('urls')
        if not urls or not isinstance(urls, list):
            return jsonify({'error': 'URLs must be provided as a list'}), 400

        logger.info(f"Processing URLs: {urls}")
        analyzer = ProductAnalyzer()
        result = analyzer.compare_products(urls)
        
        logger.info("Comparison completed successfully")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error processing comparison: {str(e)}")
        return jsonify({
            'error': 'Error processing comparison',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)