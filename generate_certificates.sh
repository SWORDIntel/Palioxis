#!/bin/bash

# PROJECT PALIOXIS: Certificate Generation Script
# This script creates the necessary certificates for mTLS communication

echo "[*] Creating Palioxis Certificate Infrastructure..."
echo "[*] Creating Certificate Authority..."

# Create the CA private key
openssl genpkey -algorithm RSA -out palioxis-ca.key

# Create a self-signed CA certificate
openssl req -new -x509 -key palioxis-ca.key -out palioxis-ca.crt -days 3650 \
    -subj "/CN=PalioxisInternalCA"

echo "[*] Creating Server Certificate..."
# Create the server private key
openssl genpkey -algorithm RSA -out palioxis-server.key

# Create a certificate signing request (CSR) for the server
openssl req -new -key palioxis-server.key -out palioxis-server.csr \
    -subj "/CN=palioxis-server"

# Sign the server CSR with your CA
openssl x509 -req -in palioxis-server.csr -CA palioxis-ca.crt -CAkey palioxis-ca.key \
    -CAcreateserial -out palioxis-server.crt -days 365

echo "[*] Creating Client Certificate..."
# Create the client private key
openssl genpkey -algorithm RSA -out palioxis-client.key

# Create a CSR for the client
openssl req -new -key palioxis-client.key -out palioxis-client.csr \
    -subj "/CN=palioxis-client-01"

# Sign the client CSR with your CA
openssl x509 -req -in palioxis-client.csr -CA palioxis-ca.crt -CAkey palioxis-ca.key \
    -CAcreateserial -out palioxis-client.crt -days 365

echo "[*] Certificate generation complete. You now have:"
echo "    - palioxis-ca.crt (Certificate Authority)"
echo "    - palioxis-server.key and palioxis-server.crt (Server identity)"
echo "    - palioxis-client.key and palioxis-client.crt (Client identity)"
echo ""
echo "IMPORTANT: Distribute the client key/certificate and the CA certificate to"
echo "           the client machine securely."
