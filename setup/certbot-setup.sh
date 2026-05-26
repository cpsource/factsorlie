#!/bin/bash
set -euo pipefail

# Certbot / Let's Encrypt setup for factsorlie.com
#
# Prerequisites:
#   - certbot installed (apt install certbot)
#   - Apache container running via docker compose (serves ACME challenges
#     from /home/ubuntu/factsorlie/.well-known through a volume mount)
#
# This script:
#   1. Issues (or renews) the TLS certificate using webroot authentication
#   2. Installs a deploy hook so Apache auto-restarts after each renewal
#   3. Enables the certbot systemd timer for automatic renewal
#
# The webroot must be /home/ubuntu/factsorlie because Apache's Docker
# volume mount maps that directory's .well-known/ to the container path
# the vhost serves for ACME challenges.

DOMAIN="factsorlie.com"
WEBROOT="/home/ubuntu/factsorlie"
COMPOSE_FILE="/home/ubuntu/factsorlie/docker-compose.yml"
HOOK_DIR="/etc/letsencrypt/renewal-hooks/deploy"
HOOK_SCRIPT="${HOOK_DIR}/restart-apache.sh"

# --- 1. Issue / renew certificate -------------------------------------------

echo "Requesting certificate for ${DOMAIN} and www.${DOMAIN}..."
certbot certonly \
    --webroot \
    -w "${WEBROOT}" \
    -d "${DOMAIN}" \
    -d "www.${DOMAIN}" \
    --non-interactive \
    --agree-tos \
    --email page.cal@gmail.com

# --- 2. Deploy hook: restart Apache after renewal ---------------------------

echo "Installing deploy hook..."
mkdir -p "${HOOK_DIR}"
cat > "${HOOK_SCRIPT}" << EOF
#!/bin/bash
docker compose -f ${COMPOSE_FILE} restart apache
EOF
chmod +x "${HOOK_SCRIPT}"

# --- 3. Enable automatic renewal timer -------------------------------------

echo "Enabling certbot timer..."
systemctl enable --now certbot.timer

# --- 4. Restart Apache to load the (possibly new) certificate ---------------

echo "Restarting Apache..."
docker compose -f "${COMPOSE_FILE}" restart apache

echo "Done. Certificate expires in ~90 days; certbot timer handles renewal."
