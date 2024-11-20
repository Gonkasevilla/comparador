from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from perplexity_analyzer import ProductAnalyzer

app = Flask(__name__, static_folder='public')
CORS(app)

# Serve static files
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# API endpoint
@app.route('/api/compare', methods=['POST'])
def compare_products():
    try:
        urls = request.json['urls']
        analyzer = ProductAnalyzer()
        result = analyzer.compare_products(urls)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)