#!/bin/sh
set -e

cd /app

# Create the database directory if needed
mkdir -p /data

# Initialize DB tables and seed admin (idempotent)
export FLASK_APP=app.py
flask seed --admin-username "${ADMIN_USERNAME:-parent}" \
           --admin-password "${ADMIN_PASSWORD:-changeme}" \
    2>/dev/null || true

# Start the server
exec gunicorn -w 1 -b 0.0.0.0:5000 "app:create_app()"
