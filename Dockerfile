FROM python:3.11-slim

LABEL maintainer="aidrak"
LABEL description="LoggiFly Helper - Webhook receiver for logging LoggiFly notifications"
LABEL version="1.0"

WORKDIR /app

# Install dependencies and tools for user management
RUN apt-get update && apt-get install -y \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir flask gunicorn

# Create data directory
RUN mkdir -p /data

# Copy application files
COPY app.py /app/
COPY entrypoint.sh /app/
COPY icon.png /app/

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 5353

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5353}/health || exit 1

# Set default environment variables
ENV PORT=5353 \
    HOST=0.0.0.0 \
    LOG_LEVEL=INFO \
    NOTIFICATIONS_LOG=/data/logs/loggifly.log \
    LOG_FORMAT=detailed \
    LOG_ROTATION=true \
    MAX_LOG_SIZE=10MB \
    BACKUP_COUNT=5 \
    WORKERS=1 \
    PUID=99 \
    PGID=100

ENTRYPOINT ["/app/entrypoint.sh"]