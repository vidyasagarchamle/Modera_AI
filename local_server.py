from flask import Flask, request, jsonify, send_file
from api.index import moderate_content
import os

app = Flask(__name__)

@app.route('/')
def home():
    return send_file('api/test.html')

@app.route('/api/index', methods=['POST', 'OPTIONS'])
def handle_moderation():
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        response = jsonify({})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 204

    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({"error": "No content provided"}), 400

        result = moderate_content(data['content'])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080) 