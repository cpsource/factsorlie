#!/bin/bash
set -e

echo "Starting factsorlie.com..."

# Start Redis and Flask first
docker compose up -d redis flask

# Use HTTP-only config so Apache can start without certs
echo "Starting Apache with HTTP-only config for certificate issuance..."
cp apache/httpd-vhosts-init.conf apache/httpd-vhosts-active.conf
docker compose up -d --build apache

# Wait for Apache to be ready
sleep 3

# Request certificates using host certbot
echo "Requesting SSL certificates from Let's Encrypt..."
if sudo certbot certonly --webroot -w /home/ubuntu/factsorlie -d factsorlie.com -d www.factsorlie.com --email admin@factsorlie.com --agree-tos --non-interactive; then
    echo "Certificates obtained successfully."
else
    echo "Failed to obtain certificates. Make sure DNS for factsorlie.com points to this server."
    exit 1
fi

# Switch to full config with SSL and restart Apache
echo "Switching to SSL config and restarting Apache..."
cp apache/httpd-vhosts.conf apache/httpd-vhosts-active.conf
docker compose restart apache

echo "All services are running."
echo "  - https://factsorlie.com"
echo "  - Flask:  http://localhost:5000"
echo "  - Redis:  localhost:6379"
