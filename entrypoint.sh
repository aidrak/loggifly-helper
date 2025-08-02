#!/bin/bash
set -e

# Install curl for health checks if not present
if ! command -v curl &> /dev/null; then
    echo "Installing curl for health checks..."
    # Note: This would require root, so we'll skip for now
    # apt-get update && apt-get install -y curl
fi

# Ensure log directory exists and is writable
LOG_DIR=$(dirname "${LOG_FILE:-/logs/loggifly-notifications.log}")
mkdir -p "$LOG_DIR"

# Test log file write permissions
if ! touch "${LOG_FILE:-/logs/loggifly-notifications.log}"; then
    echo "ERROR: Cannot write to log file ${LOG_FILE:-/logs/loggifly-notifications.log}"
    echo "Please check volume mount permissions"
    exit 1
fi

echo "LoggiFly Helper starting..."
echo "Configuration:"
echo "  Port: ${PORT:-5353}"
echo "  Host: ${HOST:-0.0.0.0}"
echo "  Log File: ${LOG_FILE:-/logs/loggifly-notifications.log}"
echo "  Log Format: ${LOG_FORMAT:-detailed}"
echo "  Log Rotation: ${LOG_ROTATION:-true}"
echo "Will log ALL notifications received from LoggiFly"

# Start the application
if [ "${WORKERS:-1}" -gt 1 ]; then
    echo "Starting with Gunicorn (${WORKERS} workers)..."
    exec gunicorn --bind "${HOST:-0.0.0.0}:${PORT:-5353}" --workers "${WORKERS}" app:app
else
    echo "Starting with Flask development server..."
    exec python /app/app.py
fi