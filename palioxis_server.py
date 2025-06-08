#!/usr/bin/env python3
# PROJECT PALIOXIS: Server Class
# This file contains the server implementation with mTLS and DPoP security

import os
import ssl
import socket
import logging
import daemon
import signal
import json
import time
import jwt
from typing import Dict, Any, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.x509 import load_pem_x509_certificate

from destroyers import get_destroyer, BaseDestroyer
from config_manager import ConfigManager


class PalioxisServer:
    """Server class for the Palioxis self-destruct system"""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize with a ConfigManager instance"""
        self.config_manager = config_manager
        self.logger = logging.getLogger('palioxis.server')
        self.settings = self.config_manager.get_server_settings()
        self.destroyer_settings = self.config_manager.get_destroyer_settings()
        self.server_socket = None
        self.ssl_context = None
        self.target_directories = self.config_manager.get_target_directories()
        
    def setup_ssl_context(self) -> bool:
        """Set up the SSL context for mTLS"""
        try:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            # Load the server's certificate and private key
            self.ssl_context.load_cert_chain(
                certfile=self.settings['server_cert'],
                keyfile=self.settings['server_key']
            )
            # Load the CA certificate to verify clients against
            self.ssl_context.load_verify_locations(cafile=self.settings['ca_cert'])
            # Enforce client certificate verification
            self.ssl_context.verify_mode = ssl.CERT_REQUIRED
            
            self.logger.info("SSL context successfully set up for mTLS")
            return True
        except Exception as e:
            self.logger.error(f"SSL context setup failed: {e}")
            return False
            
    def setup_server_socket(self) -> bool:
        """Create and configure the server socket"""
        try:
            host = self.settings['host']
            port = self.settings['port']
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            sock.listen(5)
            
            # Wrap the server socket with the SSL context
            self.server_socket = self.ssl_context.wrap_socket(sock, server_side=True)
            
            self.logger.info(f"Server socket bound to {host}:{port}")
            return True
        except Exception as e:
            self.logger.error(f"Server socket setup failed: {e}")
            return False
            
    def verify_dpop_proof(self, token: str, client_public_key, http_method: str, http_url: str) -> bool:
        """Verify the DPoP proof from the client"""
        if not token:
            self.logger.error("No DPoP token provided")
            return False
            
        try:
            # Get the unverified header to extract the JWK
            unverified_header = jwt.get_unverified_header(token)
            # Extract public key from DPoP header
            jwk = unverified_header['jwk']
            
            # Convert JWK to public key
            dpop_public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
            
            # Compare the DPoP key with the mTLS client cert key
            client_pem = client_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            dpop_pem = dpop_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            if client_pem != dpop_pem:
                self.logger.error("DPoP key does not match mTLS client certificate key")
                return False
                
            # Verify the token signature and claims
            decoded_token = jwt.decode(
                token,
                dpop_public_key,
                algorithms=[unverified_header['alg']],
                options={"verify_aud": False}  # No audience claim in DPoP
            )
            
            # Check claims
            assert decoded_token['htm'] == http_method
            assert decoded_token['htu'] == http_url
            assert time.time() - decoded_token['iat'] < 300  # Must be recent (within 5 minutes)
            
            self.logger.info("DPoP proof successfully verified")
            return True
        except Exception as e:
            self.logger.error(f"DPoP verification failed: {e}")
            return False
            
    def handle_connection(self, conn: ssl.SSLSocket, addr: tuple) -> None:
        """Handle an incoming client connection"""
        self.logger.info(f"Handling connection from {addr}")
        
        try:
            # Get the client's certificate for DPoP verification
            client_cert_der = conn.getpeercert(binary_form=True)
            client_cert = load_pem_x509_certificate(client_cert_der)
            client_public_key = client_cert.public_key()
            
            # Common name from client certificate
            client_cn = None
            for item in conn.getpeercert()['subject']:
                for key, value in item:
                    if key == 'commonName':
                        client_cn = value
                        
            self.logger.info(f"Client authenticated as: {client_cn}")
            
            # Read the HTTP-like request from the client
            request_data = conn.recv(4096).decode()
            if not request_data:
                self.logger.error("Empty request received")
                return
                
            self.logger.debug(f"Received request: {request_data[:100]}...")
            
            # Parse the HTTP-like request
            try:
                headers, body = request_data.split('\r\n\r\n', 1)
            except ValueError:
                self.logger.error("Malformed request - could not split headers and body")
                conn.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\nMalformed Request")
                return
                
            # Extract DPoP proof from headers
            dpop_proof = None
            request_method = None
            request_path = None
            
            # Parse the request line and headers
            for i, line in enumerate(headers.split('\r\n')):
                if i == 0:  # Request line
                    try:
                        request_method, request_path, _ = line.split(' ', 2)
                    except ValueError:
                        self.logger.error(f"Malformed request line: {line}")
                elif line.lower().startswith('dpop:'):
                    dpop_proof = line.split(' ', 1)[1]
            
            if not request_method or not request_path:
                self.logger.error("Missing request method or path")
                conn.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\nInvalid Request Format")
                return
                
            # Construct the full URL for DPoP verification
            host = self.settings['host']
            port = self.settings['port']
            http_url = f"https://{host}:{port}{request_path}"
            
            # Verify DPoP proof
            if not self.verify_dpop_proof(dpop_proof, client_public_key, request_method, http_url):
                self.logger.error("DPoP verification failed")
                conn.sendall(b"HTTP/1.1 401 Unauthorized\r\n\r\nInvalid DPoP Proof")
                return
                
            # Check if this is a destroy request
            if request_method == 'POST' and request_path == '/destroy':
                key = self.settings['key']
                
                if body.strip() == key:
                    self.logger.info("Valid destroy key received, initiating self-destruct")
                    conn.sendall(b"HTTP/1.1 200 OK\r\n\r\nSignal Accepted. Initiating self-destruct.")
                    
                    # Close the connection before destruction
                    conn.close()
                    
                    # Execute the self-destruction
                    self.handle_self_destruct()
                else:
                    self.logger.warning(f"Invalid destroy key received: '{body.strip()}'")
                    conn.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\nInvalid Key")
            else:
                self.logger.warning(f"Unsupported request: {request_method} {request_path}")
                conn.sendall(b"HTTP/1.1 405 Method Not Allowed\r\n\r\nUnsupported Request")
        except Exception as e:
            self.logger.error(f"Error handling connection: {e}")
            try:
                conn.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\nServer Error")
            except:
                pass
        finally:
            try:
                conn.close()
            except:
                pass
                
    def handle_self_destruct(self) -> None:
        """Handle the self-destruct signal"""
        self.logger.warning("EXECUTING SELF-DESTRUCT SEQUENCE")
        
        # Create the destroyer module based on configuration
        module_name = self.destroyer_settings['module']
        destroyer = get_destroyer(module_name, self.destroyer_settings)
        
        # Destroy all target directories
        if self.target_directories:
            self.logger.info(f"Destroying {len(self.target_directories)} target directories")
            destroyer.destroy_paths(self.target_directories)
        else:
            self.logger.warning("No target directories specified for destruction")
            
        # Handle TrueCrypt volumes if any
        self.destroy_truecrypt_volumes()
        
        # Final shutdown
        self.logger.critical("Self-destruct sequence completed. Shutting down system.")
        try:
            os.system('shutdown -h now')
        except Exception as e:
            self.logger.error(f"Failed to shutdown system: {e}")
            
    def destroy_truecrypt_volumes(self) -> None:
        """Check for and destroy any TrueCrypt volumes"""
        try:
            import subprocess
            
            # Check if TrueCrypt is installed
            try:
                subprocess.run(['truecrypt', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except (subprocess.SubprocessError, FileNotFoundError):
                self.logger.info("TrueCrypt not found, skipping TrueCrypt volume destruction")
                return
                
            # Look for mounted TrueCrypt volumes
            drives = subprocess.check_output('ls /media', shell=True).decode().split('\n')
            truecrypt_drives = [d for d in drives if d and 'truecrypt' in d]
            
            if not truecrypt_drives:
                self.logger.info("No mounted TrueCrypt volumes found")
                return
                
            # Create destroyer for TrueCrypt volumes
            destroyer = get_destroyer(self.destroyer_settings['module'], self.destroyer_settings)
            
            # Destroy each TrueCrypt volume
            for drive in truecrypt_drives:
                volume_path = f"/media/{drive}"
                self.logger.info(f"Destroying TrueCrypt volume: {volume_path}")
                destroyer.destroy_dir(volume_path)
                
            # Dismount TrueCrypt volumes
            self.logger.info("Dismounting all TrueCrypt volumes")
            subprocess.run(['truecrypt', '-d'], check=True)
            
        except Exception as e:
            self.logger.error(f"Error handling TrueCrypt volumes: {e}")
            
    def run_server(self, daemonize: bool = False) -> None:
        """Run the server, optionally as a daemon"""
        if daemonize:
            self.start_daemon()
            return
            
        self.logger.info("Starting Palioxis server in foreground mode")
        
        # Set up SSL and socket
        if not self.setup_ssl_context():
            return
        if not self.setup_server_socket():
            return
            
        self.logger.info(f"Palioxis server listening on {self.settings['host']}:{self.settings['port']}")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
        # Main server loop
        try:
            while True:
                conn, addr = self.server_socket.accept()
                self.logger.info(f"Client connected from {addr}")
                self.handle_connection(conn, addr)
        except KeyboardInterrupt:
            self.logger.info("Server interrupted, shutting down...")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
                
    def start_daemon(self) -> None:
        """Start the server as a daemon process"""
        daemon_settings = self.config_manager.get_daemon_settings()
        log_file = daemon_settings['log_file']
        
        self.logger.info(f"Starting Palioxis server as daemon, logging to {log_file}")
        
        # Configure daemon context
        context = daemon.DaemonContext(
            working_directory='/',
            umask=0o002,
            pidfile=None,
        )
        
        # Setup log file
        try:
            log_dir = os.path.dirname(os.path.abspath(log_file))
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except Exception as e:
            self.logger.error(f"Failed to create log directory: {e}")
            
        # Start the daemon
        with context:
            self.logger.info("Daemon started")
            self.run_server(daemonize=False)  # Now inside the daemon
            
    def handle_signal(self, sig, frame) -> None:
        """Handle OS signals"""
        self.logger.info(f"Received signal {sig}, shutting down...")
        if self.server_socket:
            self.server_socket.close()
        exit(0)
