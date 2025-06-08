#!/usr/bin/env python3
# PROJECT PALIOXIS: Client Class
# This file contains the client implementation for sending self-destruct signals

import os
import ssl
import socket
import logging
import json
import time
import uuid
import jwt
from typing import Dict, Any, Optional, Tuple

from cryptography.hazmat.primitives import serialization
from config_manager import ConfigManager


class PalioxisClient:
    """Client class for the Palioxis self-destruct system"""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize with a ConfigManager instance"""
        self.config_manager = config_manager
        self.logger = logging.getLogger('palioxis.client')
        self.settings = self.config_manager.get_client_settings()
        self.ssl_context = None
        
    def setup_ssl_context(self) -> bool:
        """Set up the SSL context for mTLS"""
        try:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            # Load the client's certificate and private key
            self.ssl_context.load_cert_chain(
                certfile=self.settings['client_cert'],
                keyfile=self.settings['client_key']
            )
            # Load the CA certificate to verify the server against
            self.ssl_context.load_verify_locations(cafile=self.settings['ca_cert'])
            
            self.logger.info("SSL context successfully set up for mTLS")
            return True
        except Exception as e:
            self.logger.error(f"SSL context setup failed: {e}")
            return False
            
    def generate_dpop_proof(self, private_key, http_method: str, http_url: str) -> str:
        """Generate a DPoP proof token for client authentication"""
        try:
            public_key = private_key.public_key()
            
            # Create the JWK (JSON Web Key) for the header
            jwk = {
                "kty": "RSA",
                "n": jwt.utils.base64url_encode(public_key.public_numbers().n.to_bytes(256, 'big')).decode(),
                "e": jwt.utils.base64url_encode(public_key.public_numbers().e.to_bytes(3, 'big')).decode(),
            }
            
            headers = {
                "typ": "dpop+jwt",
                "alg": "RS256",
                "jwk": jwk
            }
            
            payload = {
                "iat": int(time.time()),
                "jti": str(uuid.uuid4()),
                "htm": http_method,
                "htu": http_url,
            }
            
            token = jwt.encode(payload, private_key, algorithm="RS256", headers=headers)
            return token
        except Exception as e:
            self.logger.error(f"Error generating DPoP proof: {e}")
            raise
            
    def send_signal(self, host: str, port: int, key: str) -> Tuple[bool, str]:
        """Send a self-destruct signal to a specific server"""
        self.logger.info(f"Preparing to send signal to {host}:{port}")
        
        # Set up SSL context if not already done
        if not self.ssl_context and not self.setup_ssl_context():
            return False, "SSL context setup failed"
            
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # Wrap the client socket with the SSL context
                with self.ssl_context.wrap_socket(sock, server_hostname='palioxis-server') as ssock:
                    ssock.connect((host, port))
                    self.logger.info(f"Connected to {host}:{port} with mTLS")
                    
                    # Generate DPoP proof
                    try:
                        with open(self.settings['client_key'], "rb") as key_file:
                            key_data = key_file.read()
                            private_key = serialization.load_pem_private_key(key_data, password=None)
                        
                        http_url = f"https://{host}:{port}/destroy"
                        dpop_proof = self.generate_dpop_proof(private_key, "POST", http_url)
                    except Exception as e:
                        self.logger.error(f"Failed to generate DPoP proof: {e}")
                        return False, f"DPoP proof generation failed: {str(e)}"
                    
                    # Construct and send the HTTP-like request
                    request = (
                        f"POST /destroy HTTP/1.1\r\n"
                        f"Host: {host}:{port}\r\n"
                        f"DPoP: {dpop_proof}\r\n"
                        f"Content-Length: {len(key)}\r\n"
                        f"\r\n"
                        f"{key}"
                    )
                    
                    self.logger.debug("Sending destroy request")
                    ssock.sendall(request.encode())
                    
                    # Receive and process response
                    response = ssock.recv(1024).decode()
                    
                    if "200 OK" in response:
                        self.logger.info(f"Signal successfully sent to {host}:{port}")
                        return True, f"Signal accepted by {host}:{port}"
                    else:
                        self.logger.warning(f"Server rejected signal: {response.splitlines()[0]}")
                        return False, f"Signal rejected: {response.splitlines()[0]}"
        except Exception as e:
            self.logger.error(f"Error sending signal to {host}:{port}: {e}")
            return False, f"Connection error: {str(e)}"
            
    def send_signals_from_file(self, file_path: str) -> Dict[str, Any]:
        """Send self-destruct signals to all servers listed in a file"""
        if not os.path.exists(file_path):
            self.logger.error(f"Node list file not found: {file_path}")
            return {"success": False, "message": f"Node list file not found: {file_path}", "results": []}
            
        results = []
        success_count = 0
        failure_count = 0
        
        try:
            with open(file_path, 'r') as f:
                lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
                
            if not lines:
                self.logger.warning(f"No valid entries found in {file_path}")
                return {"success": False, "message": "No valid entries found in node list", "results": []}
                
            for i, line in enumerate(lines):
                try:
                    # Parse the line format: host port key
                    parts = line.split()
                    if len(parts) < 3:
                        self.logger.warning(f"Invalid entry format at line {i+1}: {line}")
                        results.append({
                            "host": "unknown",
                            "port": 0,
                            "success": False,
                            "message": f"Invalid entry format: {line}"
                        })
                        failure_count += 1
                        continue
                        
                    host = parts[0]
                    port = int(parts[1])
                    key = parts[2]
                    
                    self.logger.info(f"Sending signal to node {i+1}: {host}:{port}")
                    success, message = self.send_signal(host, port, key)
                    
                    result = {
                        "host": host,
                        "port": port,
                        "success": success,
                        "message": message
                    }
                    
                    results.append(result)
                    
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                        
                except Exception as e:
                    self.logger.error(f"Error processing entry at line {i+1}: {e}")
                    results.append({
                        "host": parts[0] if len(parts) > 0 else "unknown",
                        "port": int(parts[1]) if len(parts) > 1 else 0,
                        "success": False,
                        "message": f"Processing error: {str(e)}"
                    })
                    failure_count += 1
                    
            return {
                "success": success_count > 0,
                "message": f"Processed {len(results)} node(s): {success_count} succeeded, {failure_count} failed",
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Error processing node list: {e}")
            return {"success": False, "message": f"Error processing node list: {str(e)}", "results": results}
