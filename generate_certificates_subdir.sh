#!/bin/bash
# Certificate Generation Script for Palioxis with subdirectory support

# Check if subdirectory parameter is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <certificate_directory>"
    echo "Example: $0 certs/server1"
    exit 1
fi

CERT_DIR=$1

# Create directory for certificates
mkdir -p "$CERT_DIR"
echo "Creating certificates in directory: $CERT_DIR"

# Generate CA key and certificate
openssl genrsa -out "$CERT_DIR/ca.key" 4096
openssl req -new -x509 -key "$CERT_DIR/ca.key" -out "$CERT_DIR/ca.crt" -subj "/CN=PalioxisCA" -days 3650

# Generate server key and certificate request
openssl genrsa -out "$CERT_DIR/server.key" 2048
openssl req -new -key "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" -subj "/CN=PalioxisServer"

# Sign server certificate with CA
openssl x509 -req -in "$CERT_DIR/server.csr" -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" -CAcreateserial -out "$CERT_DIR/server.crt" -days 365

# Generate client key and certificate request
openssl genrsa -out "$CERT_DIR/client.key" 2048
openssl req -new -key "$CERT_DIR/client.key" -out "$CERT_DIR/client.csr" -subj "/CN=PalioxisClient"

# Sign client certificate with CA
openssl x509 -req -in "$CERT_DIR/client.csr" -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" -CAcreateserial -out "$CERT_DIR/client.crt" -days 365

# Clean up CSR files
rm "$CERT_DIR"/*.csr

echo "Certificate generation complete in $CERT_DIR."
echo "Generated files:"
echo "  - CA certificate: $CERT_DIR/ca.crt"
echo "  - Server certificate: $CERT_DIR/server.crt"
echo "  - Server key: $CERT_DIR/server.key"
echo "  - Client certificate: $CERT_DIR/client.crt"
echo "  - Client key: $CERT_DIR/client.key"
