#!/usr/bin/env python3
# PROJECT PALIOXIS: Main Script
# This script integrates all Palioxis components and provides the command-line interface

import os
import sys
import argparse
import logging
import configparser
import traceback
from typing import Dict, List, Any, Optional

# Check for required modules
try:
    import jwt
    import daemon
    from cryptography.hazmat.primitives import serialization
    from cryptography.x509 import load_pem_x509_certificate
except ImportError as e:
    print(f"[error] Required module not found: {e}")
    print("[suggestion] Install required dependencies with: pip install pyjwt cryptography python-daemon configparser")
    print("[suggestion] Consider using a virtual environment: python3 -m venv palioxis_env && source palioxis_env/bin/activate")
    sys.exit(1)

# Import local modules
from config_manager import ConfigManager
from destroyers import get_destroyer, BaseDestroyer
from palioxis_server import PalioxisServer
from palioxis_client import PalioxisClient

# Set up logging
def setup_logging(log_level='INFO', log_file=None):
    """Configure the logging system"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    if log_file:
        logging.basicConfig(level=numeric_level, format=log_format,
                           filename=log_file, filemode='a')
    else:
        logging.basicConfig(level=numeric_level, format=log_format)
    
    # Add a console handler if logging to file
    if log_file:
        console = logging.StreamHandler()
        console.setLevel(numeric_level)
        formatter = logging.Formatter(log_format)
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
        
    return logging.getLogger('palioxis')


class PalioxisApp:
    """Main application class for Palioxis"""
    
    def __init__(self):
        """Initialize the application"""
        self.config_manager = ConfigManager()
        self.logger = logging.getLogger('palioxis.app')
        self.args = None
        
    def parse_arguments(self):
        """Parse command line arguments"""
        help_text = "Palioxis: Greek personification of the backrush or retreat from battle. Linux self-destruction utility. Use with caution."
        parser = argparse.ArgumentParser(description=help_text, prog="palioxis")
        
        # Main mode arguments
        parser.add_argument('--mode', help='run as client or server', choices=['client', 'server'])
        parser.add_argument('--config', help='path to configuration file', default=None)
        
        # Server specific arguments
        parser.add_argument('--host', help='server host')
        parser.add_argument('--port', help='server port', type=int)
        parser.add_argument('--key', help='destruction key')
        parser.add_argument('--daemon', help='run server as a daemon', action='store_true')
        parser.add_argument('--install-daemon', help='install as a systemd daemon', action='store_true')
        
        # Client specific arguments
        parser.add_argument('--list', help='server list [use with client mode]')
        
        # Destroyer module selection
        parser.add_argument('--destroyer', help='destruction method: shred, fast, wipe, windows', 
                           choices=['shred', 'fast', 'wipe', 'windows'])
        
        # Certificate management
        parser.add_argument('--gen-certs', help='generate certificates for mTLS', action='store_true')
        
        # Target management
        parser.add_argument('--add-target', help='add a directory or file to targets', metavar='PATH')
        
        # Other utilities
        parser.add_argument('--log-level', help='logging level', 
                           choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO')
        
        self.args = parser.parse_args()
        return self.args
        
    def load_configuration(self):
        """Load configuration from file and/or command line args"""
        # Load config file if specified
        if self.args.config:
            self.config_manager.config_file = self.args.config
            
        self.config_manager.load_config()
        
        # Override config with command line arguments
        if self.args.host:
            self.config_manager.update('Server', 'host', self.args.host)
            
        if self.args.port:
            self.config_manager.update('Server', 'port', str(self.args.port))
            
        if self.args.key:
            self.config_manager.update('Server', 'key', self.args.key)
            
        if self.args.destroyer:
            self.config_manager.update('Destroyer', 'module', self.args.destroyer)
            
        if self.args.list:
            self.config_manager.update('Client', 'nodes_list', self.args.list)
            
        # Update log level if specified
        if self.args.log_level:
            self.config_manager.update('Daemon', 'log_level', self.args.log_level)
            
        return True
        
    def add_target_directory(self, target_path):
        """Add a target directory or file to the configuration"""
        if not os.path.exists(target_path):
            self.logger.error(f"Target path does not exist: {target_path}")
            return False
            
        # First try to update the config file
        dirs = self.config_manager.get_target_directories()
        if target_path in dirs:
            self.logger.warning(f"Target path already in configuration: {target_path}")
            return False
            
        dirs.append(target_path)
        
        # Get the existing directories configuration and append the new path
        current_dirs = self.config_manager.get('Targets', 'directories', '')
        if current_dirs:
            # Add a newline if there are already directories configured
            new_dirs = current_dirs + '\n    ' + target_path
        else:
            new_dirs = target_path
            
        self.config_manager.update('Targets', 'directories', new_dirs)
        
        # Save the updated configuration
        success = self.config_manager.save_config()
        if success:
            self.logger.info(f"Added target path to configuration: {target_path}")
        else:
            self.logger.error(f"Failed to save configuration with new target path: {target_path}")
            
            # Fall back to targets.txt if config save fails
            try:
                with open('targets.txt', 'a') as f:
                    f.write(f"\n{target_path}")
                self.logger.info(f"Added target path to targets.txt: {target_path}")
                success = True
            except Exception as e:
                self.logger.error(f"Failed to add target path to targets.txt: {e}")
                success = False
                
        return success
        
    def install_daemon(self):
        """Install Palioxis as a systemd service"""
        settings = self.config_manager.get_server_settings()
        daemon_settings = self.config_manager.get_daemon_settings()
        
        # Get the absolute path to the script
        script_path = os.path.abspath(__file__)
        
        # Create the systemd service file content
        service_content = f"""[Unit]
Description=Palioxis self-destruct server with mTLS/DPoP security
After=network.target

[Service]
Type=simple
ExecStart={sys.executable} {script_path} --mode server --config {self.config_manager.config_file}
Restart=on-failure
WorkingDirectory={os.path.dirname(script_path)}

[Install]
WantedBy=multi-user.target
"""
        
        try:
            # Write the service file
            service_path = '/etc/systemd/system/palioxis.service'
            with open(service_path, 'w') as f:
                f.write(service_content)
                
            # Reload systemd and enable the service
            os.system('systemctl daemon-reload')
            os.system('systemctl enable palioxis.service')
            
            self.logger.info("Palioxis successfully installed as a systemd daemon")
            print("[*] Palioxis installed as a daemon. Use 'systemctl start palioxis' to start it.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to install Palioxis as a daemon: {e}")
            print(f"[error] Failed to install Palioxis as a daemon: {e}")
            return False
            
    def generate_certificates(self):
        """Generate certificates for mTLS communication"""
        print("[*] Generating certificates for mTLS...")
        
        # Check if the certificate generation script exists
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generate_certificates.sh')
        
        if not os.path.exists(script_path):
            print("[error] Certificate generation script not found.")
            return False
            
        # Make the script executable
        os.chmod(script_path, 0o755)
        
        # Run the script
        result = os.system(script_path)
        
        if result == 0:
            print("[*] Certificates generated successfully.")
            return True
        else:
            print(f"[error] Certificate generation failed with code {result}.")
            return False

    def run_server(self, daemonize=False):
        """Start the Palioxis server"""
        # Initialize the server
        server = PalioxisServer(self.config_manager)
        
        # Run the server
        try:
            server.run_server(daemonize)
            return True
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            traceback.print_exc()
            return False
    
    def run_client(self):
        """Run the Palioxis client to send signals to servers"""
        client = PalioxisClient(self.config_manager)
        
        # Get the nodes list file path
        nodes_list = self.args.list or self.config_manager.get('Client', 'nodes_list')
        if not nodes_list:
            self.logger.error("No nodes list file specified")
            print("[error] Missing server list for client mode.")
            print("Usage: ./palioxis.py --mode client --list /path/to/nodes.txt")
            return False
            
        # Check if the file exists
        if not os.path.exists(nodes_list):
            self.logger.error(f"Nodes list file not found: {nodes_list}")
            print(f"[error] Host list {nodes_list} cannot be found.")
            return False
            
        # Send signals to all servers in the list
        result = client.send_signals_from_file(nodes_list)
        
        # Print the results
        print(f"\n[*] {result['message']}")
        for node_result in result['results']:
            status = "SUCCESS" if node_result['success'] else "FAILED"
            print(f"[{status}] {node_result['host']}:{node_result['port']} - {node_result['message']}")
            
        return result['success']
    
    def interactive_mode(self):
        """Interactive mode when no arguments are provided"""
        print("[*] No arguments provided. Entering interactive mode.")
        print("[*] What would you like to do?")
        print("    1. Run as server")
        print("    2. Run as client")
        print("    3. Add a directory to targets")
        print("    4. Generate certificates for mTLS")
        print("    5. Exit")
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == '1':
            print("\nServer mode requires the following information:")
            host = input("Host to bind to (default: 0.0.0.0): ").strip() or '0.0.0.0'
            port = input("Port to listen on (default: 8443): ").strip() or '8443'
            key = input("Self-destruct key: ").strip()
            destroyer = input("Destroyer module (shred, fast, wipe, windows) (default: shred): ").strip() or 'shred'
            
            if not key:
                print("[error] Self-destruct key is required.")
                return False
                
            self.config_manager.update('Server', 'host', host)
            self.config_manager.update('Server', 'port', port)
            self.config_manager.update('Server', 'key', key)
            self.config_manager.update('Destroyer', 'module', destroyer)
            self.config_manager.save_config()
            
            # Create args object for compatibility
            class Args:
                pass
            self.args = Args()
            self.args.mode = 'server'
            self.args.daemon = False
            
            return self.run_server(False)
        elif choice == '2':
            nodes_list = input("Path to nodes list file: ").strip()
            if not nodes_list:
                print("[error] Nodes list file path is required.")
                return False
                
            self.config_manager.update('Client', 'nodes_list', nodes_list)
            self.config_manager.save_config()
            
            # Create args object for compatibility
            class Args:
                pass
            self.args = Args()
            self.args.mode = 'client'
            self.args.list = nodes_list
            
            return self.run_client()
        elif choice == '3':
            target_path = input("Enter the directory or file to add to targets: ").strip()
            if not target_path:
                print("[error] No directory or file specified.")
                return False
                
            return self.add_target_directory(target_path)
        elif choice == '4':
            return self.generate_certificates()
        elif choice == '5':
            print("[*] Exiting.")
            return True
        else:
            print("[error] Invalid choice.")
            return False
    
    def run(self):
        """Main entry point for the application"""
        # Parse command line arguments
        self.parse_arguments()
        
        # Handle special cases that don't require configuration
        if self.args.gen_certs:
            return self.generate_certificates()
            
        # Load configuration
        self.load_configuration()
        
        # Set up logging
        daemon_settings = self.config_manager.get_daemon_settings()
        log_level = self.args.log_level or daemon_settings['log_level']
        log_file = daemon_settings['log_file'] if self.args.daemon else None
        setup_logging(log_level, log_file)
        
        # Handle target directory addition
        if self.args.add_target:
            return self.add_target_directory(self.args.add_target)
            
        # Install as daemon if requested
        if self.args.install_daemon:
            return self.install_daemon()
            
        # If no mode provided, enter interactive mode
        if not self.args.mode and len(sys.argv) == 1:
            return self.interactive_mode()
            
        # Run in the specified mode
        if self.args.mode == 'server':
            return self.run_server(self.args.daemon)
        elif self.args.mode == 'client':
            return self.run_client()
        else:
            print("[error] No valid mode specified. Use --mode server or --mode client")
            return False


def main():
    """Main entry point"""
    app = PalioxisApp()
    try:
        success = app.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[error] {e}")
        traceback.print_exc()
        sys.exit(1)
        
        
if __name__ == "__main__":
    main()