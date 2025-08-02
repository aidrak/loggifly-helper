#!/bin/bash
set -e

# Setup user with PUID/PGID for Unraid compatibility
PUID=${PUID:-99}
PGID=${PGID:-100}

echo "LoggiFly Helper starting..."
echo "Setting up user with PUID=$PUID and PGID=$PGID"

# Create group if it doesn't exist
if ! getent group $PGID > /dev/null 2>&1; then
    groupadd -g $PGID loggifly
else
    GROUP_NAME=$(getent group $PGID | cut -d: -f1)
    echo "Using existing group: $GROUP_NAME ($PGID)"
fi

# Create user if it doesn't exist
if ! getent passwd $PUID > /dev/null 2>&1; then
    useradd -u $PUID -g $PGID -s /bin/bash -m loggifly
else
    USER_NAME=$(getent passwd $PUID | cut -d: -f1)
    echo "Using existing user: $USER_NAME ($PUID)"
fi

# Create required directories with proper permissions
LOG_DIR=$(dirname "${LOG_FILE:-/data/logs/loggifly-notifications.log}")
echo "Creating directory structure under /data..."
mkdir -p "$LOG_DIR"
mkdir -p /data/config

# Set ownership of /data directory
chown -R $PUID:$PGID /data

# Test log file write permissions
if ! gosu $PUID:$PGID touch "${LOG_FILE:-/data/logs/loggifly-notifications.log}"; then
    echo "ERROR: Cannot write to log file ${LOG_FILE:-/data/logs/loggifly-notifications.log}"
    echo "Please check volume mount permissions"
    exit 1
fi

echo "Configuration:"
echo "  Port: ${PORT:-5353}"
echo "  Host: ${HOST:-0.0.0.0}"
echo "  Log File: ${LOG_FILE:-/data/logs/loggifly-notifications.log}"
echo "  Log Format: ${LOG_FORMAT:-detailed}"
echo "  Log Rotation: ${LOG_ROTATION:-true}"
echo "  User: $PUID:$PGID"
echo "Will log ALL notifications received from LoggiFly"

# Start the application as the specified user
if [ "${WORKERS:-1}" -gt 1 ]; then
    echo "Starting with Gunicorn (${WORKERS} workers)..."
    exec gosu $PUID:$PGID gunicorn --bind "${HOST:-0.0.0.0}:${PORT:-5353}" --workers "${WORKERS}" app:app
else
    echo "Starting with Flask development server..."
    exec gosu $PUID:$PGID python /app/app.py
fi