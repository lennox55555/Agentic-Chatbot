import os
import json
import logging
from flask import Flask, request, jsonify

# config logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='/tmp/websocket_messages.log')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/process', methods=['POST'])
def process_message():
    """Process messages sent from Lambda"""
    try:
        # get message from request body
        data = request.json
        message = data.get('message', '')
        
        logger.info(f"Received message from Lambda: {message}")
        
        response = {
            "status": "success",
            "response": f"Hi from EC2. Your message: \"{message}\"",
            "processed_by": "ec2"
        }
        
        logger.info(f"Sending response: {response}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)