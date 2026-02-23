#!/bin/bash
set -e

echo "Restarting Flask..."
docker compose restart flask
echo "Flask restarted."
