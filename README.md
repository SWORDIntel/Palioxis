# Palioxis V2 - Secure Linux Self-Destruct Utility

## Overview

Palioxis V2 is a comprehensive Linux self-destruct utility designed for secure data destruction in emergency situations. Named after the Greek personification of retreat from battle, Palioxis "salts the earth behind you" when you need to ensure data confidentiality.

This utility has been completely refactored with a modular, object-oriented architecture, enhanced security protocols, and improved usability through both a command-line interface and a text-based user interface (TUI).

## Features

### Core Features

- **Modular Architecture**: Clean separation between server, client, configuration management, and destruction operations
- **Enhanced Security**: Uses mutual TLS (mTLS) and DPoP JWT tokens for secure authentication and authorization
- **Multiple Operation Modes**:
  - Server mode: Listens for self-destruct signals
  - Client mode: Sends self-destruct signals to one or multiple servers
  - TUI mode: Text-based interface for all operations
  - Interactive mode: Command-line prompts for configuration
- **Deployment Options**:
  - Foreground process
  - Background daemon
  - Systemd service
- **Multiple Destroyer Modules**:
  - Default destroyer
  - Secure wipe with shred/wipe tools
  - TrueCrypt volume destruction

### Security Features

- **Mutual TLS Authentication**: Server and clients verify each other's identities
- **DPoP JWT Tokens**: Proof-of-possession tokens cryptographically bound to client keys
- **Flexible Configuration**: All security settings configurable via config files
- **Certificate Management**: Tools for generating and managing certificates

### User Interface

- **Text-based User Interface (TUI)**: Simple, non-curses menu-driven interface
- **Color-coded Output**: ANSI color codes for better readability
- **Confirmation Prompts**: Safety checks for destructive operations
- **Command-line Interface**: Rich set of command-line options

### Configuration Management

- **External Configuration**: Flexible configuration via palioxis.conf
- **Target Management**: Define destruction targets in targets.txt
- **Node Management**: Manage server nodes in nodes.txt
- **Certificate Management**: Generate and configure certificates in certs/

## Usage

### Command-line Interface

#### Server Mode
```
python3 palioxis.py --mode server --host 0.0.0.0 --port 8443
```
This will start Palioxis as a server, listening for self-destruct signals on the specified host and port. When a valid signal is received, it will destroy the specified files and directories.

#### Daemon Mode
```
python3 palioxis.py --mode server --daemon
```
Runs the server as a background daemon process.

#### Systemd Installation
```
sudo python3 palioxis.py --install-daemon
```
Installs Palioxis as a systemd service for automatic startup.

#### Client Mode
```
python3 palioxis.py --mode client --list nodes.txt
```
Sends self-destruct signals to all servers listed in nodes.txt.

```
python3 palioxis.py --mode client --host 192.168.1.100 --port 8443 --key SECRET_KEY
```
Sends a self-destruct signal to a specific server.

#### Interactive Mode
```
python3 palioxis.py
```
Starts an interactive session that guides you through configuration options.

### Text-based User Interface (TUI)
```
python3 palioxis_tui.py
```
Launches the TUI with menus for:
- Server Operations
- Client Operations
- Configuration Management
- Certificate Management
- Deployment Management

### Certificate Generation
```
./generate_certificates.sh
```
Generates CA, server, and client certificates for mTLS.

For creating certificates in a subdirectory:
```
./generate_certificates_subdir.sh certs/node01
```

## Configuration

### Configuration File (palioxis.conf)
```
[Server]
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
```

### Node List File (nodes.txt)
```
# Format: <host> <port> <key>
192.168.1.100 8443 secret_key1
192.168.1.101 8443 secret_key2
```

### Target Directories File (targets.txt)
```
# Each line is a directory or file to be destroyed
/path/to/sensitive/data
/path/to/important/file.txt
```

## Security Considerations

- Keep certificate files secure
- Use strong authentication keys
- Run the server with appropriate permissions
- Test thoroughly before deployment
- Consider physical security implications

## Requirements

- Python 3.6+
- pyjwt
- cryptography
- python-daemon
- configparser
- OpenSSL for certificate generation

## Deployment

Creating a deployment package:
```
python3 palioxis_tui.py
```
Select Deployment Management > Create Deployment Package

## For Use By

For use by freedom fighters as needed for self-preservation, or if you want to securely delete sensitive data.

100% to be operated with full situational awareness. 
You might lose data, but that's the point.
# Palioxis V2 - Secure Linux Self-Destruct Utility

## Overview

Palioxis V2 is a comprehensive Linux self-destruct utility designed for secure data destruction in emergency situations. Named after the Greek personification of retreat from battle, Palioxis "salts the earth behind you" when you need to ensure data confidentiality.

This utility has been completely refactored with a modular, object-oriented architecture, enhanced security protocols, and improved usability through both a command-line interface and a text-based user interface (TUI).

## Features

### Core Features

- **Modular Architecture**: Clean separation between server, client, configuration management, and destruction operations
- **Enhanced Security**: Uses mutual TLS (mTLS) and DPoP JWT tokens for secure authentication and authorization
- **Multiple Operation Modes**:
  - Server mode: Listens for self-destruct signals
  - Client mode: Sends self-destruct signals to one or multiple servers
  - TUI mode: Text-based interface for all operations
  - Interactive mode: Command-line prompts for configuration
- **Deployment Options**:
  - Foreground process
  - Background daemon
  - Systemd service
- **Multiple Destroyer Modules**:
  - Default destroyer
  - Secure wipe with shred/wipe tools
  - TrueCrypt volume destruction

### Security Features

- **Mutual TLS Authentication**: Server and clients verify each other's identities
- **DPoP JWT Tokens**: Proof-of-possession tokens cryptographically bound to client keys
- **Flexible Configuration**: All security settings configurable via config files
- **Certificate Management**: Tools for generating and managing certificates

### User Interface

- **Text-based User Interface (TUI)**: Simple, non-curses menu-driven interface
- **Color-coded Output**: ANSI color codes for better readability
- **Confirmation Prompts**: Safety checks for destructive operations
- **Command-line Interface**: Rich set of command-line options

### Configuration Management

- **External Configuration**: Flexible configuration via palioxis.conf
- **Target Management**: Define destruction targets in targets.txt
- **Node Management**: Manage server nodes in nodes.txt
- **Certificate Management**: Generate and configure certificates in certs/

## Usage

### Command-line Interface

#### Server Mode
```
python3 palioxis.py --mode server --host 0.0.0.0 --port 8443
```
This will start Palioxis as a server, listening for self-destruct signals on the specified host and port. When a valid signal is received, it will destroy the specified files and directories.

#### Daemon Mode
```
python3 palioxis.py --mode server --daemon
```
Runs the server as a background daemon process.

#### Systemd Installation
```
sudo python3 palioxis.py --install-daemon
```
Installs Palioxis as a systemd service for automatic startup.

#### Client Mode
```
python3 palioxis.py --mode client --list nodes.txt
```
Sends self-destruct signals to all servers listed in nodes.txt.

```
python3 palioxis.py --mode client --host 192.168.1.100 --port 8443 --key SECRET_KEY
```
Sends a self-destruct signal to a specific server.

#### Interactive Mode
```
python3 palioxis.py
```
Starts an interactive session that guides you through configuration options.

### Text-based User Interface (TUI)
```
python3 palioxis_tui.py
```
Launches the TUI with menus for:
- Server Operations
- Client Operations
- Configuration Management
- Certificate Management
- Deployment Management

### Certificate Generation
```
./generate_certificates.sh
```
Generates CA, server, and client certificates for mTLS.

For creating certificates in a subdirectory:
```
./generate_certificates_subdir.sh certs/node01
```

## Configuration

### Configuration File (palioxis.conf)
```
[Server]
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
```

### Node List File (nodes.txt)
```
# Format: <host> <port> <key>
192.168.1.100 8443 secret_key1
192.168.1.101 8443 secret_key2
```

### Target Directories File (targets.txt)
```
# Each line is a directory or file to be destroyed
/path/to/sensitive/data
/path/to/important/file.txt
```

## Security Considerations

- Keep certificate files secure
- Use strong authentication keys
- Run the server with appropriate permissions
- Test thoroughly before deployment
- Consider physical security implications

## Requirements

- Python 3.6+
- pyjwt
- cryptography
- python-daemon
- configparser
- OpenSSL for certificate generation

## Deployment

Creating a deployment package:
```
python3 palioxis_tui.py
```
Select Deployment Management > Create Deployment Package

## For Use By

For use by freedom fighters as needed for self-preservation, or if you want to securely delete sensitive data.

100% to be operated with full situational awareness. 
You might lose data, but that's the point.
