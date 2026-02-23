#!/bin/bash
set -e

echo "Stopping factsorlie.com..."

docker compose down

echo "All services stopped."
