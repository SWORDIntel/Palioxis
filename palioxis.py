import os
import sys
import socket
import argparse
import commands

# Reading directories from targets.txt	
def load_dirs():
    with open('targets.txt', 'r') as file:
        return [line.strip() for line in file.readlines() if line.strip()]

dirs = load_dirs()

def start_server(host, port):
    print('\n[*] Starting server...')
    print(f'Host:\t{host}')
    print(f'Port:\t{port}')
    print(f'Key:\t{key}')

    socksize = 4096
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((host, port))
        server.listen(5)
    except Exception as e:
        print(f'[error] Failed to start server: {str(e)}')
        sys.exit(1)

    daemon()
    conn, addr = server.accept()
    conn.send(b'[*] established.')
    while True:
        cmd = conn.recv(socksize).decode()
        if cmd == key:
            conn.send(b'[*] received.')
            handle_signal()
            break

    conn.close()

def send_signal(host, port, dkey):
    socksize = 4096
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))
    except Exception as e:
        print(f'[error] Problem connecting to node {host}:{port} - {str(e)}')
        return

    while True:
        c = client.recv(socksize).decode()
        if c == 'established':
            client.sendall(dkey.encode())
        if c == '[*] received.':
            print('[*] Signal sent successfully.')
            break

    client.close()

def daemon(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    try: 
        pid = os.fork() 
        if pid > 0:
            sys.exit(0) 
    except OSError as e: 
        print(f"[error] fork one failed: {e.errno} ({e.strerror})")
        sys.exit(1)

    os.chdir("/") 
    os.setsid() 
    os.umask(0) 

    try: 
        pid = os.fork() 
        if pid > 0:
            print(f"[*] Palioxis PID: {pid}")
            sys.exit(0) 
    except OSError as e: 
        print(f"[error] fork two failed: {e.errno} ({e.strerror})")
        sys.exit(1)

    sys.stdin = open(stdin, 'r')
    sys.stdout = open(stdout, 'a+')
    sys.stderr = open(stderr, 'a+')

def destroy_dirs(path):
    for f in os.listdir(path):
        full_path = os.path.join(path, f)
        if os.path.isfile(full_path):
            os.popen(f'shred -n 9 -z -f -u {full_path}')
        elif os.path.isdir(full_path):
            destroy_dirs(full_path)

def destroy_tc():
    try:
        drives = commands.getoutput('ls /media').split('\n')
        for d in drives:
            if 'truecrypt' in d:
                destroy_dirs(f'/media/{d}')
                os.popen('truecrypt -d')
    except:
        pass

def handle_signal():
    for p in dirs:
        destroy_dirs(p)
    destroy_tc()
    os.popen('shutdown -h now')

# Systemd daemon installation
def install_daemon():
    service_content = f"""
[Unit]
Description=Palioxis self-destruct server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/palioxis.py --mode server --host {args.host} --port {args.port} --key {args.key}
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""
    with open('/etc/systemd/system/palioxis.service', 'w') as f:
        f.write(service_content)
    os.system('systemctl daemon-reload')
    os.system('systemctl enable palioxis.service')
    print('[*] Palioxis installed as a daemon.')

def add_directory_to_targets():
    dir_to_add = input("Enter the directory or file to add to targets.txt: ").strip()
    if dir_to_add:
        with open('targets.txt', 'a') as f:
            f.write(f"{dir_to_add}\n")
        print(f"[*] {dir_to_add} added to targets.txt")
    else:
        print("[error] Invalid input, no directory added.")

# Argument parsing
help = """Palioxis: Greek personification of the backrush or retreat from battle. Linux self-destruction utility. Use with caution."""
parser = argparse.ArgumentParser(description=help, prog="palioxis")
parser.add_argument('--mode', help='run as client or server', choices=['client', 'server'])
parser.add_argument('--host', help='server host')
parser.add_argument('--port', help='server port', type=int)
parser.add_argument('--key', help='destruction key')
parser.add_argument('--list', help='server list [use with client mode]')
parser.add_argument('--install-daemon', help='Install as a systemd daemon', action='store_true')
args = parser.parse_args()

# If no arguments provided, ask what the user wants to do
if len(sys.argv) == 1:
    print("[*] No arguments provided.")
    action = input("Do you want to run as (1) server, (2) client, or (3) add a new directory to targets.txt? (Enter 1, 2, or 3): ").strip()
    
    if action == '1':
        print("Usage: ./palioxis.py --mode server --host <host> --port <port> --key <key>")
        sys.exit(1)
    elif action == '2':
        print("Usage: ./palioxis.py --mode client --list /path/to/nodes.txt")
        sys.exit(1)
    elif action == '3':
        add_directory_to_targets()
        sys.exit(0)
    else:
        print("[error] Invalid selection.")
        sys.exit(1)

# Daemon installation
if args.install_daemon and args.mode == 'server':
    install_daemon()
    sys.exit(0)

# Running the appropriate mode
mode = args.mode
key = args.key

if mode == 'server':
    if not args.host or not args.port or not args.key:
        print("[error] Missing required arguments for server mode.")
        print("Usage: ./palioxis.py --mode server --host <host> --port <port> --key <key>")
        sys.exit(1)
    start_server(args.host, args.port)

elif mode == 'client':
    if not args.list:
        print("[error] Missing server list for client mode.")
        print("Usage: ./palioxis.py --mode client --list /path/to/nodes.txt")
        sys.exit(1)
    if os.path.exists(args.list):
        with open(args.list, 'r') as fin:
            for line in fin.readlines():
                if line.strip():
                    try:
                        entry = line.strip().split(' ')
                        print(f'[*] Attempting to signal {entry[0]}:{entry[1]}')
                        send_signal(entry[0], int(entry[1]), entry[2])
                    except Exception as e:
                        print(f'[error] {str(e)}')
                        continue
    else:
        print(f'[error] Host list {args.list} cannot be found.')
	
