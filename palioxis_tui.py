#!/usr/bin/env python3
# Palioxis TUI: Simple Text-based User Interface for Palioxis

import os
import sys
import time
import subprocess
from typing import Dict, List, Callable

# Import local modules
try:
    from config_manager import ConfigManager
    from palioxis_server import PalioxisServer
    from palioxis_client import PalioxisClient
except ImportError:
    print("[error] Cannot import required modules. Make sure you're in the Palioxis directory.")
    sys.exit(1)

# ANSI color codes for a more visually pleasing interface
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Main TUI class
class PalioxisTUI:
    def __init__(self):
        """Initialize the TUI"""
        self.config_manager = ConfigManager()
        self.running = True
        self.menu_stack = []
        
        # Default configuration values
        self.config = {
            'host': '0.0.0.0',
            'port': 8443,
            'ca_cert': 'certs/ca.crt',
            'server_cert': 'certs/server.crt',
            'server_key': 'certs/server.key',
            'client_cert': 'certs/client.crt',
            'client_key': 'certs/client.key',
            'target_dirs': ['targets.txt'],
            'nodes_file': 'nodes.txt',
            'log_file': 'palioxis.log',
            'log_level': 'INFO'
        }
        
        # Try to load config
        try:
            self.load_config()
        except Exception as e:
            print(f"[warning] Could not load config: {e}")
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def print_header(self):
        """Print the Palioxis header"""
        self.clear_screen()
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}               PALIOXIS CONTROL INTERFACE               {Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}")
        print(f"{Colors.YELLOW}Greek personification of the backrush or retreat from battle.{Colors.END}")
        print(f"{Colors.YELLOW}Linux self-destruction utility with Tier 2 Security.{Colors.END}")
        print(f"{Colors.RED}{Colors.BOLD}USE WITH CAUTION - ALL ACTIONS ARE FINAL{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}\n")
        
    def print_menu(self, title: str, options: List[Dict[str, str]], show_back: bool = True):
        """Print a menu with numbered options"""
        print(f"{Colors.BLUE}{Colors.BOLD}{title}{Colors.END}\n")
        
        for i, option in enumerate(options, 1):
            print(f"{Colors.GREEN}{i}.{Colors.END} {option['text']}")
            
        if show_back and self.menu_stack:
            print(f"{Colors.RED}b.{Colors.END} Back to previous menu")
            
        print(f"{Colors.RED}q.{Colors.END} Quit")
        print()
        
    def get_choice(self, max_choice: int) -> str:
        """Get user input for menu choice"""
        while True:
            choice = input(f"{Colors.BOLD}Enter your choice: {Colors.END}").strip().lower()
            if choice == 'q':
                return choice
            elif choice == 'b' and self.menu_stack:
                return choice
            try:
                num_choice = int(choice)
                if 1 <= num_choice <= max_choice:
                    return str(num_choice)
            except ValueError:
                pass
            print(f"{Colors.RED}Invalid choice. Please try again.{Colors.END}")
    
    def main_menu(self):
        """Display the main menu"""
        options = [
            {"text": "Server Operations", "action": self.server_menu},
            {"text": "Client Operations", "action": self.client_menu},
            {"text": "Configuration Management", "action": self.config_menu},
            {"text": "Certificate Management", "action": self.cert_menu},
            {"text": "Deployment Management", "action": self.deployment_menu},
        ]
        
        self.print_header()
        self.print_menu("MAIN MENU", options, show_back=False)
        
        choice = self.get_choice(len(options))
        if choice == 'q':
            self.running = False
        else:
            action = options[int(choice) - 1]["action"]
            self.menu_stack.append(self.main_menu)
            action()
            
    def server_menu(self):
        """Display server operations menu"""
        options = [
            {"text": "Start server in foreground", "action": self.start_server_foreground},
            {"text": "Start server as daemon", "action": self.start_server_daemon},
            {"text": "Install server as systemd service", "action": self.install_server_systemd},
            {"text": "View server status", "action": self.view_server_status},
        ]
        
        self.print_header()
        self.print_menu("SERVER OPERATIONS", options)
        
        choice = self.get_choice(len(options))
        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.menu_stack.pop()()
        else:
            action = options[int(choice) - 1]["action"]
            self.menu_stack.append(self.server_menu)
            action()
    
    def client_menu(self):
        """Display client operations menu"""
        options = [
            {"text": "Send signal to a single server", "action": self.send_single_signal},
            {"text": "Send signals using node list", "action": self.send_signals_from_file},
            {"text": "Create/Edit node list", "action": self.edit_node_list},
        ]
        
        self.print_header()
        self.print_menu("CLIENT OPERATIONS", options)
        
        choice = self.get_choice(len(options))
        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.menu_stack.pop()()
        else:
            action = options[int(choice) - 1]["action"]
            self.menu_stack.append(self.client_menu)
            action()
    
    def config_menu(self):
        """Display configuration management menu"""
        options = [
            {"text": "Edit configuration file", "action": self.edit_config_file},
            {"text": "Add target directory", "action": self.add_target_directory},
            {"text": "List target directories", "action": self.list_target_directories},
            {"text": "Set destroyer module", "action": self.set_destroyer_module},
        ]
        
        self.print_header()
        self.print_menu("CONFIGURATION MANAGEMENT", options)
        
        choice = self.get_choice(len(options))
        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.menu_stack.pop()()
        else:
            action = options[int(choice) - 1]["action"]
            self.menu_stack.append(self.config_menu)
            action()
            
    def cert_menu(self):
        """Display certificate management menu"""
        options = [
            {"text": "Generate new certificates", "action": self.generate_certificates},
            {"text": "View certificate information", "action": self.view_certificates},
        ]
        
        self.print_header()
        self.print_menu("CERTIFICATE MANAGEMENT", options)
        
        choice = self.get_choice(len(options))
        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.menu_stack.pop()()
        else:
            action = options[int(choice) - 1]["action"]
            self.menu_stack.append(self.cert_menu)
            action()
            
    def deployment_menu(self):
        """Display deployment management menu"""
        options = [
            {"text": "Create deployment package", "action": self.create_deployment_package},
            {"text": "Show deployment instructions", "action": self.show_deployment_instructions},
        ]
        
        self.print_header()
        self.print_menu("DEPLOYMENT MANAGEMENT", options)
        
        choice = self.get_choice(len(options))
        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.menu_stack.pop()()
        else:
            action = options[int(choice) - 1]["action"]
            self.menu_stack.append(self.deployment_menu)
            action()
    
    # -------------- Server Operations --------------
    
    def start_server_foreground(self):
        """Start Palioxis server in foreground mode"""
        self.print_header()
        print(f"{Colors.BLUE}{Colors.BOLD}Starting Server in Foreground{Colors.END}\n")
        
        # Get server parameters
        host = input(f"Enter host address [{self.config['host']}]: ").strip() or self.config['host']
        
        try:
            port = int(input(f"Enter port [{self.config['port']}]: ").strip() or self.config['port'])
        except ValueError:
            print(f"{Colors.RED}Invalid port number. Using default.{Colors.END}")
            port = int(self.config['port'])
        
        print(f"\n{Colors.YELLOW}Starting server at {host}:{port}{Colors.END}")
        print(f"{Colors.YELLOW}Press Ctrl+C to stop the server{Colors.END}\n")
        
        try:
            # Create server instance
            server = PalioxisServer(
                host=host, 
                port=port,
                ca_cert=self.config['ca_cert'],
                cert_file=self.config['server_cert'],
                key_file=self.config['server_key'],
                target_dirs=self.config['target_dirs']
            )
            
            print(f"{Colors.GREEN}Server initialized. Starting...{Colors.END}")
            server.start()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Server stopped by user{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}Error starting server: {e}{Colors.END}")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
    
    def start_server_daemon(self):
        """Start Palioxis server as a daemon"""
        self.print_header()
        print(f"{Colors.BLUE}{Colors.BOLD}Starting Server as Daemon{Colors.END}\n")
        
        # Get server parameters
        host = input(f"Enter host address [{self.config['host']}]: ").strip() or self.config['host']
        
        try:
            port = int(input(f"Enter port [{self.config['port']}]: ").strip() or self.config['port'])
        except ValueError:
            print(f"{Colors.RED}Invalid port number. Using default.{Colors.END}")
            port = int(self.config['port'])
        
        log_file = input(f"Enter log file [{self.config['log_file']}]: ").strip() or self.config['log_file']
        
        print(f"\n{Colors.YELLOW}Starting daemon at {host}:{port}{Colors.END}")
        print(f"{Colors.YELLOW}Logs will be written to {log_file}{Colors.END}\n")
        
        # Execute palioxis.py with daemon flags
        cmd = f"python3 palioxis.py --mode server --host {host} --port {port} --daemon --log-file {log_file}"
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"\n{Colors.GREEN}Server daemon started successfully{Colors.END}")
        except subprocess.CalledProcessError as e:
            print(f"\n{Colors.RED}Error starting server daemon: {e}{Colors.END}")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
    
    def install_server_systemd(self):
        """Install Palioxis server as a systemd service"""
        self.print_header()
        print(f"{Colors.BLUE}{Colors.BOLD}Installing Server as Systemd Service{Colors.END}\n")
        
        # Get server parameters
        host = input(f"Enter host address [{self.config['host']}]: ").strip() or self.config['host']
        
        try:
            port = int(input(f"Enter port [{self.config['port']}]: ").strip() or self.config['port'])
        except ValueError:
            print(f"{Colors.RED}Invalid port number. Using default.{Colors.END}")
            port = int(self.config['port'])
        
        print(f"\n{Colors.YELLOW}Installing systemd service for {host}:{port}{Colors.END}")
        
        cmd = f"sudo python3 palioxis.py --install-daemon --mode server --host {host} --port {port}"
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"\n{Colors.GREEN}Systemd service installed successfully{Colors.END}")
            print(f"{Colors.GREEN}Service name: palioxis.service{Colors.END}")
            print(f"{Colors.YELLOW}To start: sudo systemctl start palioxis.service{Colors.END}")
            print(f"{Colors.YELLOW}To enable at boot: sudo systemctl enable palioxis.service{Colors.END}")
        except subprocess.CalledProcessError as e:
            print(f"\n{Colors.RED}Error installing systemd service: {e}{Colors.END}")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
    
    def view_server_status(self):
        """View Palioxis server status"""
        self.print_header()
        print(f"{Colors.BLUE}{Colors.BOLD}Server Status{Colors.END}\n")
        
        try:
            # Check if systemd service is running
            result = subprocess.run("systemctl is-active palioxis.service", shell=True, capture_output=True, text=True)
            if result.stdout.strip() == "active":
                print(f"{Colors.GREEN}Systemd service: RUNNING{Colors.END}")
            else:
                print(f"{Colors.RED}Systemd service: NOT RUNNING{Colors.END}")
                
            # Check for any running Python process with palioxis
            result = subprocess.run("ps aux | grep '[p]alioxis.py'", shell=True, capture_output=True, text=True)
            if result.stdout.strip():
                print(f"\n{Colors.GREEN}Found running Palioxis processes:{Colors.END}")
                print(result.stdout)
            else:
                print(f"\n{Colors.RED}No Palioxis processes found running{Colors.END}")
                
        except Exception as e:
            print(f"\n{Colors.RED}Error checking server status: {e}{Colors.END}")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
    
    # -------------- Client Operations --------------
    
    def send_single_signal(self):
        """Send a self-destruct signal to a single server"""
        self.print_header()
        print(f"{Colors.RED}{Colors.BOLD}CAUTION: SENDING A SELF-DESTRUCT SIGNAL{Colors.END}\n")
        print(f"{Colors.RED}This action will trigger irreversible data destruction on the target server.{Colors.END}")
        confirm = input(f"\n{Colors.BOLD}Are you absolutely sure you want to continue? (yes/NO): {Colors.END}").strip().lower()
        
        if confirm != "yes":
            print(f"\n{Colors.YELLOW}Operation cancelled.{Colors.END}")
            input("\nPress Enter to return to menu...")
            self.menu_stack.pop()()
            return
        
        # Get target server details
        host = input("Enter target server host: ").strip()
        if not host:
            print(f"\n{Colors.RED}Host cannot be empty.{Colors.END}")
            input("\nPress Enter to return to menu...")
            self.menu_stack.pop()()
            return
            
        try:
            port = int(input("Enter target server port: ").strip())
        except ValueError:
            print(f"\n{Colors.RED}Invalid port number.{Colors.END}")
            input("\nPress Enter to return to menu...")
            self.menu_stack.pop()()
            return
        
        # Secret key as additional verification
        secret_key = input("Enter secret key for verification: ").strip()
        if not secret_key:
            print(f"\n{Colors.RED}Secret key cannot be empty.{Colors.END}")
            input("\nPress Enter to return to menu...")
            self.menu_stack.pop()()
            return
            
        print(f"\n{Colors.YELLOW}Sending self-destruct signal to {host}:{port}...{Colors.END}")
        
        try:
            # Create client instance
            client = PalioxisClient(
                ca_cert=self.config['ca_cert'],
                cert_file=self.config['client_cert'],
                key_file=self.config['client_key']
            )
            
            # Send the signal
            success = client.send_signal(host, port, secret_key)
            
            if success:
                print(f"\n{Colors.GREEN}Signal sent successfully.{Colors.END}")
            else:
                print(f"\n{Colors.RED}Failed to send signal.{Colors.END}")
                
        except Exception as e:
            print(f"\n{Colors.RED}Error sending signal: {e}{Colors.END}")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
    
    def send_signals_from_file(self):
        """Send self-destruct signals to multiple servers from a nodes list file"""
        self.print_header()
        print(f"{Colors.RED}{Colors.BOLD}CAUTION: SENDING SELF-DESTRUCT SIGNALS TO MULTIPLE SERVERS{Colors.END}\n")
        print(f"{Colors.RED}This action will trigger irreversible data destruction on ALL target servers.{Colors.END}")
        confirm = input(f"\n{Colors.BOLD}Are you absolutely sure you want to continue? (yes/NO): {Colors.END}").strip().lower()
        
        if confirm != "yes":
            print(f"\n{Colors.YELLOW}Operation cancelled.{Colors.END}")
            input("\nPress Enter to return to menu...")
            self.menu_stack.pop()()
            return
        
        # Get nodes list file
        nodes_file = input(f"Enter nodes list file path [{self.config['nodes_file']}]: ").strip() or self.config['nodes_file']
        
        if not os.path.exists(nodes_file):
            print(f"\n{Colors.RED}Nodes list file not found: {nodes_file}{Colors.END}")
            input("\nPress Enter to return to menu...")
            self.menu_stack.pop()()
            return
        
        print(f"\n{Colors.YELLOW}Sending self-destruct signals to all servers in {nodes_file}...{Colors.END}")
        
        try:
            # Create client instance
            client = PalioxisClient(
                ca_cert=self.config['ca_cert'],
                cert_file=self.config['client_cert'],
                key_file=self.config['client_key']
            )
            
            # Send signals from file
            success_count, total = client.send_signals_from_file(nodes_file)
            
            print(f"\n{Colors.GREEN}Signals sent: {success_count}/{total}{Colors.END}")
                
        except Exception as e:
            print(f"\n{Colors.RED}Error sending signals: {e}{Colors.END}")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
    
    def edit_node_list(self):
        """Create or edit a node list file"""
        self.print_header()
        print(f"{Colors.BLUE}{Colors.BOLD}Edit Nodes List{Colors.END}\n")
        
        nodes_file = input(f"Enter nodes list file path [{self.config['nodes_file']}]: ").strip() or self.config['nodes_file']
        
        if os.path.exists(nodes_file):
            print(f"\n{Colors.YELLOW}Existing nodes file found. Current content:{Colors.END}")
            try:
                with open(nodes_file, 'r') as f:
                    content = f.read()
                    print(f"\n{content}")
            except Exception as e:
                print(f"\n{Colors.RED}Error reading file: {e}{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}Creating new nodes file: {nodes_file}{Colors.END}")
        
        print(f"\n{Colors.BLUE}Enter nodes in format: <host> <port> <key>{Colors.END}")
        print(f"{Colors.BLUE}One node per line. Enter empty line to finish.{Colors.END}\n")
        
        nodes = []
        while True:
            node = input("Node (or empty to finish): ").strip()
            if not node:
                break
                
            # Validate format
            parts = node.split()
            if len(parts) != 3:
                print(f"{Colors.RED}Invalid format. Use: <host> <port> <key>{Colors.END}")
                continue
                
            try:
                int(parts[1])  # Check if port is a number
                nodes.append(node)
            except ValueError:
                print(f"{Colors.RED}Invalid port number.{Colors.END}")
        
        if nodes:
            try:
                with open(nodes_file, 'w') as f:
                    f.write('\n'.join(nodes))
                print(f"\n{Colors.GREEN}Nodes list saved to {nodes_file}{Colors.END}")
            except Exception as e:
                print(f"\n{Colors.RED}Error saving file: {e}{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}No nodes added. File not modified.{Colors.END}")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
        
    # -------------- Configuration Management --------------
    
    def load_config(self):
        """Load configuration from config file"""
        try:
            config = self.config_manager.load_config()
            if config:
                # Update our config with values from the file
                for section in config.sections():
                    for key, value in config[section].items():
                        if key in self.config:
                            if key == 'target_dirs':
                                self.config[key] = value.split(',')
                            else:
                                self.config[key] = value
                return True
            return False
        except Exception as e:
            print(f"[error] Failed to load configuration: {e}")
            return False
    
    def edit_config_file(self):
        """Edit the configuration file"""
        self.print_header()
        print(f"{Colors.BLUE}{Colors.BOLD}Edit Configuration File{Colors.END}\n")
        
        config_file = input("Enter configuration file path [palioxis.conf]: ").strip() or "palioxis.conf"
        
        if os.path.exists(config_file):
            print(f"\n{Colors.YELLOW}Existing configuration file found.{Colors.END}")
            try:
                editor = os.environ.get('EDITOR', 'nano')
                subprocess.run([editor, config_file], check=True)
                print(f"\n{Colors.GREEN}Configuration saved.{Colors.END}")
                # Reload configuration
                self.load_config()
            except Exception as e:
                print(f"\n{Colors.RED}Error editing configuration: {e}{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}Creating new configuration file: {config_file}{Colors.END}")
            try:
                # Create a basic configuration file
                with open(config_file, 'w') as f:
                    f.write("""[Server]
host = 0.0.0.0
port = 8443

[Client]
nodes_file = nodes.txt

[Security]
ca_cert = certs/ca.crt
server_cert = certs/server.crt
server_key = certs/server.key
client_cert = certs/client.crt
client_key = certs/client.key

[Destruction]
target_dirs = targets.txt

[Logging]
log_file = palioxis.log
log_level = INFO
""")
                    
                editor = os.environ.get('EDITOR', 'nano')
                subprocess.run([editor, config_file], check=True)
                print(f"\n{Colors.GREEN}Configuration saved.{Colors.END}")
                # Load the new configuration
                self.load_config()
            except Exception as e:
                print(f"\n{Colors.RED}Error creating configuration: {e}{Colors.END}")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
    
    def add_target_directory(self):
        """Add a directory to the targets list"""
        self.print_header()
        print(f"{Colors.BLUE}{Colors.BOLD}Add Target Directory{Colors.END}\n")
        
        targets_file = input("Enter targets file path [targets.txt]: ").strip() or "targets.txt"
        
        # Check if file exists, if not create it
        if not os.path.exists(targets_file):
            open(targets_file, 'w').close()
            print(f"{Colors.YELLOW}Created new targets file: {targets_file}{Colors.END}")
        
        # Show current targets
        print(f"\n{Colors.BLUE}Current target directories:{Colors.END}")
        try:
            with open(targets_file, 'r') as f:
                targets = f.read().strip().split('\n')
                if targets and targets[0]:
                    for i, target in enumerate(targets, 1):
                        print(f"{Colors.GREEN}{i}.{Colors.END} {target}")
                else:
                    print(f"{Colors.YELLOW}No targets defined yet.{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}Error reading targets file: {e}{Colors.END}")
            targets = []
        
        # Add new target
        new_target = input("\nEnter path to add to targets (or empty to cancel): ").strip()
        if new_target:
            if os.path.exists(new_target):
                try:
                    with open(targets_file, 'a') as f:
                        f.write(f"{new_target}\n")
                    print(f"\n{Colors.GREEN}Added {new_target} to targets.{Colors.END}")
                except Exception as e:
                    print(f"\n{Colors.RED}Error adding target: {e}{Colors.END}")
            else:
                print(f"\n{Colors.RED}Warning: Path {new_target} does not exist. Adding anyway.{Colors.END}")
                try:
                    with open(targets_file, 'a') as f:
                        f.write(f"{new_target}\n")
                    print(f"{Colors.GREEN}Added {new_target} to targets.{Colors.END}")
                except Exception as e:
                    print(f"{Colors.RED}Error adding target: {e}{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}No target added.{Colors.END}")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
    
    def list_target_directories(self):
        """List all target directories"""
        self.print_header()
        print(f"{Colors.BLUE}{Colors.BOLD}Target Directories{Colors.END}\n")
        
        targets_file = input("Enter targets file path [targets.txt]: ").strip() or "targets.txt"
        
        if not os.path.exists(targets_file):
            print(f"\n{Colors.YELLOW}Targets file not found: {targets_file}{Colors.END}")
            input("\nPress Enter to return to menu...")
            self.menu_stack.pop()()
            return
        
        # Show targets with details
        print(f"\n{Colors.BLUE}Target directories in {targets_file}:{Colors.END}\n")
        try:
            with open(targets_file, 'r') as f:
                targets = f.read().strip().split('\n')
                if targets and targets[0]:
                    for i, target in enumerate(targets, 1):
                        status = "exists" if os.path.exists(target) else "not found"
                        status_color = Colors.GREEN if os.path.exists(target) else Colors.RED
                        print(f"{Colors.GREEN}{i}.{Colors.END} {target} - {status_color}({status}){Colors.END}")
                else:
                    print(f"{Colors.YELLOW}No targets defined.{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}Error reading targets file: {e}{Colors.END}")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
    
    def set_destroyer_module(self):
        """Select a destroyer module"""
        self.print_header()
        print(f"{Colors.BLUE}{Colors.BOLD}Set Destroyer Module{Colors.END}\n")
        
        # Get available destroyer modules
        destroyers = [
            "default", 
            "secure_wipe",
            "truecrypt",
        ]
        
        print(f"{Colors.BLUE}Available destroyer modules:{Colors.END}\n")
        for i, module in enumerate(destroyers, 1):
            print(f"{Colors.GREEN}{i}.{Colors.END} {module}")
        
        try:
            choice = int(input(f"\n{Colors.BOLD}Select destroyer module (1-{len(destroyers)}): {Colors.END}").strip())
            if 1 <= choice <= len(destroyers):
                selected = destroyers[choice-1]
                print(f"\n{Colors.GREEN}Selected destroyer: {selected}{Colors.END}")
                
                # Update configuration file
                config_file = "palioxis.conf"
                if os.path.exists(config_file):
                    config = configparser.ConfigParser()
                    config.read(config_file)
                    
                    if 'Destruction' not in config:
                        config['Destruction'] = {}
                    
                    config['Destruction']['destroyer'] = selected
                    
                    with open(config_file, 'w') as f:
                        config.write(f)
                        
                    print(f"{Colors.GREEN}Updated configuration with {selected} destroyer.{Colors.END}")
                else:
                    print(f"{Colors.YELLOW}Configuration file not found. Creating new one.{Colors.END}")
                    config = configparser.ConfigParser()
                    config['Destruction'] = {'destroyer': selected}
                    
                    with open(config_file, 'w') as f:
                        config.write(f)
                        
                    print(f"{Colors.GREEN}Created configuration with {selected} destroyer.{Colors.END}")
            else:
                print(f"\n{Colors.RED}Invalid choice.{Colors.END}")
        except ValueError:
            print(f"\n{Colors.RED}Invalid input.{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}Error setting destroyer: {e}{Colors.END}")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
    
    # -------------- Certificate Management --------------
    
    def generate_certificates(self):
        """Generate new mTLS certificates"""
        self.print_header()
        print(f"{Colors.BLUE}{Colors.BOLD}Generate New Certificates{Colors.END}\n")
        
        print(f"{Colors.YELLOW}This will generate new CA, server, and client certificates for mTLS.{Colors.END}")
        confirm = input(f"\n{Colors.BOLD}Are you sure you want to continue? (yes/NO): {Colors.END}").strip().lower()
        
        if confirm != "yes":
            print(f"\n{Colors.YELLOW}Certificate generation cancelled.{Colors.END}")
            input("\nPress Enter to return to menu...")
            self.menu_stack.pop()()
            return
        
        # Create certs directory if needed
        if not os.path.exists("certs"):
            os.makedirs("certs")
            print(f"{Colors.GREEN}Created certificates directory.{Colors.END}")
        
        print(f"\n{Colors.YELLOW}Generating certificates...{Colors.END}")
        try:
            # Run the certificate generation script
            subprocess.run(["./generate_certificates.sh"], check=True)
            print(f"\n{Colors.GREEN}Certificates generated successfully!{Colors.END}")
            print(f"{Colors.GREEN}Files saved in the certs/ directory:{Colors.END}")
            print(f"  - {Colors.BLUE}ca.crt{Colors.END} - Certificate Authority cert")
            print(f"  - {Colors.BLUE}server.crt{Colors.END} - Server certificate")
            print(f"  - {Colors.BLUE}server.key{Colors.END} - Server private key")
            print(f"  - {Colors.BLUE}client.crt{Colors.END} - Client certificate")
            print(f"  - {Colors.BLUE}client.key{Colors.END} - Client private key")
        except FileNotFoundError:
            print(f"\n{Colors.RED}Certificate generation script not found.{Colors.END}")
            print(f"{Colors.YELLOW}Creating generate_certificates.sh script...{Colors.END}")
            
            # Create the certificate generation script
            with open("generate_certificates.sh", "w") as f:
                f.write("""#!/bin/bash
# Certificate Generation Script for Palioxis

# Create directory for certificates
mkdir -p certs
cd certs

# Generate CA key and certificate
openssl genrsa -out ca.key 4096
openssl req -new -x509 -key ca.key -out ca.crt -subj "/CN=PalioxisCA" -days 3650

# Generate server key and certificate request
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=PalioxisServer"

# Sign server certificate with CA
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365

# Generate client key and certificate request
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "/CN=PalioxisClient"

# Sign client certificate with CA
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365

# Clean up CSR files
rm *.csr

echo "Certificate generation complete."
""")
            os.chmod("generate_certificates.sh", 0o755)
            
            print(f"{Colors.GREEN}Script created. Running it now...{Colors.END}")
            subprocess.run(["./generate_certificates.sh"], check=True)
            print(f"\n{Colors.GREEN}Certificates generated successfully!{Colors.END}")
        except subprocess.CalledProcessError as e:
            print(f"\n{Colors.RED}Error generating certificates: {e}{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}Error: {e}{Colors.END}")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
    
    def view_certificates(self):
        """View certificate information"""
        self.print_header()
        print(f"{Colors.BLUE}{Colors.BOLD}Certificate Information{Colors.END}\n")
        
        cert_dir = "certs"
        if not os.path.exists(cert_dir):
            print(f"{Colors.RED}Certificate directory not found.{Colors.END}")
            print(f"{Colors.YELLOW}You need to generate certificates first.{Colors.END}")
            input("\nPress Enter to return to menu...")
            self.menu_stack.pop()()
            return
        
        cert_files = [f for f in os.listdir(cert_dir) if f.endswith('.crt')]
        if not cert_files:
            print(f"{Colors.RED}No certificate files found in {cert_dir}/{Colors.END}")
            print(f"{Colors.YELLOW}You need to generate certificates first.{Colors.END}")
            input("\nPress Enter to return to menu...")
            self.menu_stack.pop()()
            return
        
        for cert_file in cert_files:
            print(f"{Colors.GREEN}Certificate: {cert_file}{Colors.END}")
            try:
                result = subprocess.run(["openssl", "x509", "-in", f"{cert_dir}/{cert_file}", "-text", "-noout"], 
                                        capture_output=True, text=True, check=True)
                
                # Extract and display important information
                output = result.stdout
                lines = output.split('\n')
                
                # Display subject, issuer, validity
                print(f"  {Colors.BLUE}Details:{Colors.END}")
                for line in lines:
                    if any(key in line for key in ["Subject:", "Issuer:", "Not Before:", "Not After :"]):
                        print(f"  {line.strip()}")
                print()
            except subprocess.CalledProcessError as e:
                print(f"  {Colors.RED}Error reading certificate: {e}{Colors.END}\n")
            except Exception as e:
                print(f"  {Colors.RED}Error: {e}{Colors.END}\n")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
    
    # -------------- Deployment Management --------------
    
    def create_deployment_package(self):
        """Create a deployment package for distribution"""
        self.print_header()
        print(f"{Colors.BLUE}{Colors.BOLD}Create Deployment Package{Colors.END}\n")
        
        package_name = input("Enter package name [palioxis-package]: ").strip() or "palioxis-package"
        include_certs = input("Include certificates? (yes/NO): ").strip().lower() == "yes"
        
        print(f"\n{Colors.YELLOW}Creating deployment package {package_name}.tar.gz...{Colors.END}")
        
        try:
            # Create temporary directory
            os.makedirs(package_name, exist_ok=True)
            
            # Copy required files
            files_to_copy = [
                "palioxis.py",
                "palioxis_server.py",
                "palioxis_client.py",
                "config_manager.py",
                "destroyers.py",
                "palioxis_tui.py",
                "generate_certificates.sh",
                "README.md"
            ]
            
            for file in files_to_copy:
                if os.path.exists(file):
                    subprocess.run(["cp", file, package_name], check=True)
            
            # Create example configs
            with open(f"{package_name}/palioxis.conf.example", "w") as f:
                f.write("""[Server]
host = 0.0.0.0
port = 8443

[Client]
nodes_file = nodes.txt

[Security]
ca_cert = certs/ca.crt
server_cert = certs/server.crt
server_key = certs/server.key
client_cert = certs/client.crt
client_key = certs/client.key

[Destruction]
target_dirs = targets.txt
destroyer = secure_wipe

[Logging]
log_file = palioxis.log
log_level = INFO
""")
            
            with open(f"{package_name}/nodes.txt.example", "w") as f:
                f.write("""# Example nodes file
# Format: <host> <port> <key>
localhost 8443 secret_key
192.168.1.100 8443 another_key
""")
                
            with open(f"{package_name}/targets.txt.example", "w") as f:
                f.write("""# Example targets file
# Each line is a directory or file to be destroyed
/path/to/directory/to/destroy
/path/to/sensitive/file.txt
""")
            
            # Include certificates if requested
            if include_certs and os.path.exists("certs"):
                subprocess.run(["cp", "-r", "certs", package_name], check=True)
            
            # Create package
            subprocess.run(["tar", "-czf", f"{package_name}.tar.gz", package_name], check=True)
            
            # Clean up temporary directory
            subprocess.run(["rm", "-rf", package_name], check=True)
            
            print(f"\n{Colors.GREEN}Package created: {package_name}.tar.gz{Colors.END}")
                
        except Exception as e:
            print(f"\n{Colors.RED}Error creating package: {e}{Colors.END}")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()
    
    def show_deployment_instructions(self):
        """Show instructions for deploying Palioxis"""
        self.print_header()
        print(f"{Colors.BLUE}{Colors.BOLD}Deployment Instructions{Colors.END}\n")
        
        print(f"{Colors.YELLOW}=== Installing Palioxis ==={Colors.END}")
        print("1. Extract the Palioxis package:")
        print("   tar -xzf palioxis-package.tar.gz")
        print("   cd palioxis-package\n")
        
        print("2. Install dependencies:")
        print("   pip install pyjwt cryptography python-daemon configparser\n")
        
        print("3. Generate certificates (if not included):")
        print("   chmod +x generate_certificates.sh")
        print("   ./generate_certificates.sh\n")
        
        print("4. Create configuration:")
        print("   cp palioxis.conf.example palioxis.conf")
        print("   nano palioxis.conf  # Edit settings as needed\n")
        
        print("5. Create target directories file:")
        print("   cp targets.txt.example targets.txt")
        print("   nano targets.txt  # Add directories to destroy\n")
        
        print(f"{Colors.YELLOW}=== Running Palioxis ==={Colors.END}")
        print("- As a server:")
        print("  python3 palioxis.py --mode server --host 0.0.0.0 --port 8443\n")
        
        print("- As a daemon:")
        print("  python3 palioxis.py --mode server --daemon\n")
        
        print("- As a systemd service:")
        print("  sudo python3 palioxis.py --install-daemon\n")
        
        print("- As a client:")
        print("  python3 palioxis.py --mode client --list nodes.txt\n")
        
        print("- Using the TUI:")
        print("  python3 palioxis_tui.py\n")
        
        print(f"{Colors.YELLOW}=== Security Considerations ==={Colors.END}")
        print("- Keep certificate files secure")
        print("- Use strong keys for authentication")
        print("- Run server with appropriate permissions")
        print("- Test the system thoroughly before relying on it")
        
        input("\nPress Enter to return to menu...")
        self.menu_stack.pop()()


def main():
    """Main function to run the Palioxis TUI"""
    tui = PalioxisTUI()
    
    try:
        while tui.running:
            tui.main_menu()
    except KeyboardInterrupt:
        print("\n\nExiting Palioxis TUI...")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        traceback.print_exc()
        
    print("\nThank you for using Palioxis.")
    

if __name__ == "__main__":
    main()
